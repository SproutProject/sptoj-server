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

    def bind(self, key, source_cls):
        target_cls = self.target_cls
        pkey = target_cls._symbols[target_cls._pname].obj
        self.rkey = sa.Column('_rel_{}'.format(key), pkey.type,
            sa.ForeignKey(pkey, onupdate=self.onupdate, ondelete=self.ondelete),
            index=True)

        if self.back_populates is not None:
            assert self.back_populates not in self.target_cls._relations
            self.target_cls._relations[self.back_populates] = Relation(
                source_cls, rkey=self.rkey, reverse=True)

        return self.rkey


class Symbol(object):

    def __init__(self, obj, immutable, primary):

        self.obj = obj
        self.immutable = immutable
        self.primary = primary


class ShadowColumn(object):

    def __init__(self, cls, mapping, prefix):

        self.cls = cls
        self.mapping = mapping
        self.prefix = prefix

    def __getattr__(self, name):

        column = getattr(self.cls, name)
        if isinstance(column, sa.Column):
            name = self.prefix + column.name
            if name in self.mapping:
                return self.mapping[name]
        elif isinstance(column, ShadowColumn):
            return ShadowColumn(column.cls, self.mapping,
                '{}__{}_'.format(self.prefix, name))

        raise AttributeError


class ShadowMeta(type):

    def build_relation_query(table, relations):

        query = table
        label_map = {}
        for key, relation in relations.items():
            prefix = '__' + key
            target_cls = relation.target_cls
            target_query = target_cls._relquery.alias(prefix)

            for column in target_query.columns:
                label_map[column] = '{}_{}'.format(prefix, column.name)

            query = query.join(target_query,
                relation.rkey == target_query.columns[target_cls._pname])

        relation_columns = {}
        select_columns = []
        for column in query.columns:
            if column.name.startswith('_rel_'):
                continue

            if column in label_map:
                labeled_column = column.label(label_map[column])
                relation_columns[labeled_column.name] = column
                column = labeled_column

            select_columns.append(column)

        return (relation_columns, sa.select(select_columns, from_obj=query))

    def __new__(cls, name, bases, namespace):

        model_cls = type.__new__(cls, name, bases, namespace)

        if name == 'BaseModel':
            return model_cls

        pname = None
        symbols = {}
        columns = {}
        relations = {}
        pkey_constraint = None

        attrs = list(model_cls.__dict__.items())
        for key, value in attrs:
            if key == '__primarykey__':
                pkey_constraint = sa.PrimaryKeyConstraint(
                    *[column.name for column in value])
                continue

            if (not isinstance(value, Relation) and
                not isinstance(value, sa.Column)):
                continue

            immutable = False
            primary = False
            name = key
            if key.startswith('_'):
                name = name.lstrip('_')
                immutable = True

            if isinstance(value, Relation):
                relations[name] = value
            elif isinstance(value, sa.Column):
                columns[name] = value
                primary = value.primary_key

            if primary:
                assert pname is None
                pname = name

            symbols[name] = Symbol(value, immutable, primary)
            delattr(model_cls, key)

        model_cls._pname = pname

        table_columns = list(columns.values())
        for key, relation in relations.items():
            table_columns.append(relation.bind(key, model_cls))

        if pkey_constraint is not None:
            table_columns.append(pkey_constraint)

        model_cls._columns = columns
        model_cls._relations = relations
        model_cls._symbols = symbols
        model_cls._table = sa.Table(namespace['__tablename__'],
            model_cls._metadata, *table_columns)
        model_cls._relcolumns, model_cls._relquery = cls.build_relation_query(
            model_cls._table, relations)

        return model_cls

    def __getattr__(self, name):

        if name not in self._symbols:
            raise AttributeError

        symbol = self._symbols[name]
        if isinstance(symbol.obj, sa.Column):
            return symbol.obj   
        elif isinstance(symbol.obj, Relation):
            relation = symbol.obj
            if not relation.reverse:
                return ShadowColumn(relation.target_cls, self._relcolumns,
                    '__{}_'.format(name))

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
        
        if self.typ is None:
            return result
        else:
            return self.typ(result)

    async def first(self):

        result = await self.results.fetchone()
        self.results.close()

        if result is None:
            return None
        elif self.typ is None:
            return result
        else:
            return self.typ(result)

    async def scalar(self):

        result = await self.results.scalar()
        if result is None:
            return None
        elif self.typ is None:
            return result
        else:
            return self.typ(result)


class BaseModel(object, metaclass=ShadowMeta):

    _metadata = MetaData()

    def __init__(self, _result_obj=None, _prefix='', **kwargs):

        if _result_obj is not None:
            fields = dict((key, _result_obj[_prefix + column.name])
                for key, column in self._columns.items())

            for key, relation in self._relations.items():
                if not relation.reverse:
                    target_cls = relation.target_cls
                    next_prefix = '{}__{}_'.format(_prefix, key)
                    fields[key] = target_cls(_result_obj, next_prefix)
        else:
            fields = {}
            for key, column in self._columns.items():
                value = None
                if key in kwargs:
                    value = kwargs[key]
                elif key != self._pname:
                    raise AttributeError
                
                fields[key] = value

            for key, relation in self._relations.items():
                if not relation.reverse and key in kwargs:
                    fields[key] = kwargs[key]

        object.__setattr__(self, '_fields', fields)

        if self._pname is not None:
            self.update_reverse_relations()

    def __getattr__(self, name):

        return self._fields[name]

    def __setattr__(self, name, value):

        override_mutable = False
        if name.startswith('_'):
            name = name.lstrip('_')
            override_mutable = True

        symbol = self._symbols.get(name)
        if symbol is None:
            raise AttributeError

        if symbol.primary:
            raise AttributeError

        if symbol.immutable and not override_mutable:
            raise AttributeError

        if isinstance(symbol.obj, Relation):
            relation = symbol.obj
            if relation.reverse:
                raise AttributeError

        self._fields[name] = value

    def update_reverse_relations(self):

        pval = self._fields[self._pname]
        reverse_relations = [(key, relation) for key, relation
            in self._relations.items() if relation.reverse]

        if pval is None:
            for key, relation in reverse_relations:
                if key in self._fields:
                    del self._fields[key]
        else:
            for key, relation in reverse_relations:
                self._fields[key] = (relation.target_cls.select()
                    .where(relation.rkey == pval))

    async def save(self, conn):

        table_fields = {}

        for key, column in self._columns.items():
            if key not in self._fields:
                raise AttributeError

            if key == self._pname and self._fields[key] is None:
                continue

            table_fields[column.name] = self._fields[key]

        for key, relation in self._relations.items():
            if relation.reverse:
                continue

            if key not in self._fields:
                raise AttributeError

            target = self._fields[key]
            target_pval = getattr(target, target._pname)
            assert target_pval is not None

            table_fields[relation.rkey.name] = target_pval

        expr = (sa.dialects.postgresql.insert(self._table)
            .values(**table_fields)
            .on_conflict_do_update(
                constraint=self._table.primary_key,
                set_=table_fields
            ))

        if self._pname is not None:
            pkey = self._symbols[self._pname].obj
            expr = expr.returning(pkey)

        result = await conn.execute(expr)

        if self._pname is not None:
            pval = await result.scalar()
            assert pval is not None
            self._fields[self._pname] = pval
            # Since we may change the primary value, update reversed relation
            # queries.
            self.update_reverse_relations()

    @classmethod
    def select(cls):

        return ShadowExpr(cls._relquery, typ=cls)

    @classmethod
    def delete(cls):

        return ShadowExpr(cls._table.delete())

    @classmethod
    def join(cls, other, *args, **kwargs):

        return ShadowExpr(cls._table.join(other._table, *args, **kwargs))


def select(fields, cls=None):

    query_fields = []
    for field in fields:
        if isinstance(field, BaseModel):
            field = field._table

        query_fields.append(field)

    return ShadowExpr(sa.select(query_fields), typ=cls)


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

    # Make sure to load all schemas.
    import model.user
    import model.problem
    import model.proset
    import model.challenge

    engine = sa.create_engine(db_url)
    BaseModel._metadata.create_all(engine)
    engine.dispose()


def drop_schemas(db_url):

    # Make sure to load all schemas.
    import model.user
    import model.problem
    import model.proset
    import model.challenge

    engine = sa.create_engine(db_url)
    BaseModel._metadata.drop_all(engine)
    engine.dispose()
