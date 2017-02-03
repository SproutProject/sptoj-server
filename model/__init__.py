'''Model base module'''


import config
import redis
import asyncio
import sqlalchemy as sa
from sqlalchemy import MetaData


class BaseModel:

    metadata = MetaData()

    def __init__(self, **kwargs):

        object.__setattr__(self, '_fields', {})

        pkey = None
        for column in self.table.columns:
            if column.primary_key:
                pkey = column

            value = None
            if column.name in kwargs:
                value = kwargs[column.name]
            elif not column.primary_key:
                raise AttributeError

            self._fields[column.name] = value

        assert pkey is not None
        object.__setattr__(self, '_pkey', pkey)

    def __getattr__(self, name):

        if name not in self._fields:
            raise AttributeError

        return self._fields[name]

    def __setattr__(self, name, value):

        if name not in self._fields or name == self._pkey.name:
            raise AttributeError

        self._fields[name] = value

    def save(self):

        fields = dict(self._fields)
        del fields[self._pkey.name]

        pval = self._fields[self._pkey.name]
        table = self.table
        if pval is None:
            return table.insert().values(**fields)
        else:
            return table.update().where(self._pkey == pval).values(**fields)

    def delete(self):

        pval = self._fields[self._pkey.name]
        if pval is None:
            raise AttributeError

        return self.table.delete().where(self._pkey == pval)


def model_context(func):

    async def wrapper(*args, **kwargs):
        '''Wrapper.'''

        conn = asyncio.Task.current_task()._conn
        return await func(*args, **kwargs, conn=conn)

    return wrapper


def create_schemas(db_url):

    engine = sa.create_engine(db_url)
    BaseModel.metadata.create_all(engine)
    engine.dispose()


def drop_schemas(db_url):

    engine = sa.create_engine(db_url)
    BaseModel.metadata.drop_all(engine)
    engine.dispose()
