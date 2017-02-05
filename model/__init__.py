'''Model base module'''


import config
import redis
import collections
import asyncio
import sqlalchemy as sa
from sqlalchemy import MetaData


class Relation(object):

    def __init__(self, target_cls, back_populates=None, onupdate="CASCADE",
        ondelete="CASCADE", rkey=None, reverse=False):

        self.target_cls = target_cls
        self.back_populates = back_populates
        self.onupdate = onupdate
        self.ondelete = ondelete
        self.rkey = rkey
        self.reverse = reverse

    def bind(self, source_cls):
        self.rkey = sa.Column('_rel_{}'.format(self.target_cls._table.name),
            self.target_cls._pkey.type,
            sa.ForeignKey(self.target_cls._pkey, onupdate=self.onupdate,
                ondelete=self.ondelete),
            index=True)

        if self.back_populates is not None:
            assert self.back_populates not in self.target_cls._relations
            self.target_cls._relations[self.back_populates] = Relation(
                source_cls, rkey=self.rkey, reverse=True)

        return self.rkey


class ShadowMeta(type):

    def find_related_tables(relations):

        workqueue = collections.deque([relations])
        # There is no reference to itself
        visited = set()

        while len(workqueue) > 0:
            for relation in workqueue.popleft().values():
                if relation.reverse:
                    continue

                target_cls = relation.target_cls
                if target_cls not in visited:
                    visited.add(target_cls)
                    workqueue.append(relation.target_cls._relations)

        return set(cls._table for cls in visited)

    def __new__(cls, name, bases, namespace):

        model_cls = type.__new__(cls, name, bases, namespace)

        if name == 'BaseModel':
            return model_cls

        pkey = None
        pfield = None
        columns = {}
        relations = {}
        for key, value in model_cls.__dict__.items():
            if isinstance(value, Relation):
                relations[key] = value
            elif isinstance(value, sa.Column):
                columns[key] = value
                if value.primary_key:
                    assert pkey is None
                    pkey = value
                    pfield = key

        assert pkey is not None
        model_cls._pkey = pkey
        model_cls._pfield = pfield

        table_columns = list(columns.values())
        for relation in relations.values():
            table_columns.append(relation.bind(model_cls))

        for key in columns.keys():
            delattr(model_cls, key)

        for key in relations.keys():
            delattr(model_cls, key)

        model_cls._columns = columns
        model_cls._relations = relations
        model_cls._reltables = cls.find_related_tables(relations)

        model_cls._table = sa.Table(namespace['__tablename__'],
            model_cls._metadata, *table_columns)

        return model_cls

    def __getattr__(self, name):

        if name in self._table.columns:
            return self._table.columns[name]

        raise AttributeError


class ShadowExpr(object):

    def __init__(self, expr, typ=None):

        self.expr = expr
        self.typ = typ

    def __getattr__(self, name):

        func = getattr(self.expr, name)

        def wrapper(*args, **kwargs):
            '''Wrapper.'''

            proxy_args = []
            for value in args:
                proxy_args.append(self.proxy_value(value))

            proxy_kwargs = {}
            for key, value in kwargs.items():
                proxy_kwargs[key] = self.proxy_value(value)

            return ShadowExpr(func(*proxy_args, **proxy_kwargs), typ=self.typ)

        return wrapper

    def proxy_value(self, value):

        if isinstance(value, ShadowExpr):
            return value.expr
        elif isinstance(value, ShadowMeta):
            return value._table

        return value

    async def execute(self, conn):

        results = await conn.execute(self.expr)
        return ShadowResult(results, self.typ)


class ShadowResult(object):

    def __init__(self, results, typ):

        self.results = results
        self.rowcount = self.results.rowcount
        self.typ = typ

    def __aiter__(self):

        return self

    async def __anext__(self):

        result = await self.results.fetchone()
        if result is None:
            raise StopAsyncIteration
        
        return self.typ(result)

    async def first(self):

        result = await self.results.fetchone()
        self.results.close()

        if result is None:
            return None
        else:
            return self.typ(result)


class BaseModel(object, metaclass=ShadowMeta):

    _metadata = MetaData()

    def __init__(self, _result_obj=None, _prefix='', **kwargs):

        if _result_obj is not None:
            fields = dict((column.name, _result_obj[_prefix + column.name])
                for column in self._columns.values())
            for key, relation in self._relations.items():
                if not relation.reverse:
                    target_cls = relation.target_cls
                    fields[key] = target_cls(_result_obj,
                        '_ns_{}_'.format(target_cls._table.name))
        else:
            fields = {}
            for column in self._columns.values():
                value = None
                try:
                    value = kwargs[column.name]
                except KeyError:
                    if not column.primary_key:
                        raise AttributeError
                
                fields[column.name] = value

            for key, relation in self._relations.items():
                if not relation.reverse and key in kwargs:
                    fields[key] = kwargs[key]

            pval = fields[self._pfield]
            if pval is not None:
                for key, relation in self._relations.items():
                    if relation.reverse:
                        fields[key] = (relation.target_cls.select()
                            .where(relation.rkey == pval))

        object.__setattr__(self, '_fields', fields)

    def __getattr__(self, name):

        if name not in self._fields:
            raise AttributeError

        return self._fields[name]

    def __setattr__(self, name, value):

        if name == self._pkey.name:
            raise AttributeError

        if name not in self._fields and name not in self._relations:
            raise AttributeError

        if name in self._relations:
            if self._relations[name].reverse:
                raise AttributeError

        self._fields[name] = value

    async def save(self, conn):

        table_fields = dict(self._fields)
        if table_fields[self._pkey.name] is None:
            del table_fields[self._pkey.name]

        for key, relation in self._relations.items():
            if relation.reverse:
                if key in self._fields:
                    del table_fields[key]
            else:
                if key not in self._fields:
                    raise AttributeError

                del table_fields[key]

                target = self._fields[key]
                target_pval = getattr(target, target._pfield)
                assert target_pval is not None

                table_fields[relation.rkey.name] = target_pval

        expr = (sa.dialects.postgresql.insert(self._table)
            .values(**table_fields)
            .on_conflict_do_update(
                index_elements=[self._pkey],
                set_=table_fields
            )).returning(self._pkey)

        pval = await (await conn.execute(expr)).scalar()
        assert pval is not None
        self._fields[self._pkey.name] = pval

        # Update reversed relation queries.
        for key, relation in self._relations.items():
            if relation.reverse:
                self._fields[key] = (relation.target_cls.select()
                    .where(relation.rkey == pval))

    @classmethod
    def select(cls):

        expr = cls._table
        table_columns = list(cls._table.columns)
        for table in cls._reltables:
            expr = expr.join(table)
            table_columns.extend(column.label('_ns_{}_{}'.format(
                table.name, column.name)) for column in table.columns)

        expr = sa.select(table_columns, from_obj=expr)
        return ShadowExpr(expr, typ=cls)

    @classmethod
    def delete(cls):

        return ShadowExpr(cls._table.delete())

    @classmethod
    def join(cls, other, *args, **kwargs):

        return ShadowExpr(cls._table.join(other._table, *args, **kwargs))


def model_context(func):

    class Context:
        def __init__(self, conn, redis):
            self.conn = conn
            self.redis = redis

    async def wrapper(*args, **kwargs):
        '''Wrapper.'''

        task = asyncio.Task.current_task()
        ctx = Context(task._conn, task._redis)
        return await func(*args, **kwargs, ctx=ctx)

    return wrapper


def create_schemas(db_url):

    engine = sa.create_engine(db_url)
    BaseModel._metadata.create_all(engine)
    engine.dispose()


def drop_schemas(db_url):

    engine = sa.create_engine(db_url)
    BaseModel._metadata.drop_all(engine)
    engine.dispose()
