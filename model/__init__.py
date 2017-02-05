'''Model base module'''


import config
import redis
import asyncio
import sqlalchemy as sa
from sqlalchemy import MetaData


class ShadowMeta(type):

    def __getattr__(self, name):
        if name in self.table.columns:
            return self.table.columns[name]

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
            return value.table

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

    metadata = MetaData()

    def __init__(self, _result_obj=None, **kwargs):

        if _result_obj is not None:
            fields = dict((column.name, _result_obj[column])
                for column in self.table.columns)
        else:
            fields = {}
            for column in self.table.columns:
                value = None
                try:
                    value = kwargs[column.name]
                except KeyError:
                    if not column.primary_key:
                        raise AttributeError
                
                fields[column.name] = value

        object.__setattr__(self, '_fields', fields)

        object.__setattr__(self, '_pkey',
            next(column for column in self.table.columns if column.primary_key))

    def __getattr__(self, name):
        if name not in self._fields:
            raise AttributeError

        return self._fields[name]

    def __setattr__(self, name, value):

        if name not in self._fields or name == self._pkey.name:
            raise AttributeError

        self._fields[name] = value

    async def save(self, conn):
        fields = dict(self._fields)
        if fields[self._pkey.name] is None:
            del fields[self._pkey.name]

        expr = (sa.dialects.postgresql.insert(self.table)
            .values(**fields)
            .on_conflict_do_update(
                index_elements=[self._pkey],
                set_=fields
            )).returning(self._pkey)

        pval = await (await conn.execute(expr)).scalar()
        assert pval is not None
        self._fields[self._pkey.name] = pval

    @classmethod
    def select(cls):

        return ShadowExpr(cls.table.select(), typ=cls)

    @classmethod
    def delete(cls):

        return ShadowExpr(cls.table.delete())

    @classmethod
    def join(cls, other, *args, **kwargs):

        return ShadowExpr(cls.table.join(other.table, *args, **kwargs))


def select(model_list):

    return ShadowExpr(sa.select([model.table for model in model_list]))


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
    BaseModel.metadata.create_all(engine)
    engine.dispose()


def drop_schemas(db_url):

    engine = sa.create_engine(db_url)
    BaseModel.metadata.drop_all(engine)
    engine.dispose()
