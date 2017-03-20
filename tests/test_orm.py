'''ORM unittest'''


import tests
from model import *
from unittest import TestCase
from sqlalchemy import Table, Column, Integer, String, Enum
from sqlalchemy.dialects.postgresql import JSONB


class AModel(BaseModel):
    '''Test A Model.'''

    __tablename__ = 'A'

    uid = Column('uid', Integer, primary_key=True)
    data = Column('data', Integer)


class BModel(BaseModel):
    '''Test B Model.'''

    __tablename__ = 'B'

    uid = Column('uid', Integer, primary_key=True)
    name = Column('name', String)
    parent = Relation(AModel, back_populates='children')
    _data = Column('data', Integer)


class TestBasic(TestCase):
    '''Basic unittest.'''

    @tests.async_test
    @model_context
    async def test_insert(self, ctx):
        '''Test insert.'''

        a = AModel(data=10)
        b = BModel(name='b', parent=a, data=20)

        with self.assertRaises(Exception):
            await b.save(ctx.conn)

        await a.save(ctx.conn)
        await b.save(ctx.conn)

    @tests.async_test
    @model_context
    async def test_select(self, ctx):
        '''Test select.'''

        a = AModel(data=10)
        b1 = BModel(name='b1', parent=a, data=20)
        b2 = BModel(name='b2', parent=a, data=30)

        await a.save(ctx.conn)
        await b1.save(ctx.conn)
        await b2.save(ctx.conn)

        rb = (await (await BModel.select()
            .where(BModel.uid == b1.uid)
            .execute(ctx.conn)).first())
        self.assertEqual(rb.name, 'b1')
        self.assertEqual(rb.data, 20)
        self.assertEqual(rb.parent.data, 10)

        rb = (await (await BModel.select()
            .where(BModel.name == 'b2')
            .execute(ctx.conn)).first())
        self.assertEqual(rb.name, 'b2')
        self.assertEqual(rb.data, 30)
        self.assertEqual(rb.parent.data, 10)

        results = (await BModel.select()
            .where(BModel.parent.data == 10)
            .execute(ctx.conn))
        rows = []
        async for rb in results:
            rows.append(rb)

        self.assertEqual(len(rows), 2)

    @tests.async_test
    @model_context
    async def test_update(self, ctx):
        '''Test update.'''

        a1 = AModel(data=10)
        a2 = AModel(data=20)
        b = BModel(name='b', parent=a1, data=20)

        await a1.save(ctx.conn)
        await a2.save(ctx.conn)
        await b.save(ctx.conn)

        with self.assertRaises(Exception):
            b.data = 30

        b.parent = a2
        b.name = 'bb'
        b._data = 30
        await b.save(ctx.conn)

        rb = (await (await BModel.select()
            .where(BModel.uid == b.uid)
            .execute(ctx.conn)).first())
        self.assertEqual(rb.name, 'bb')
        self.assertEqual(rb.data, 30)
        self.assertEqual(rb.parent.data, 20)
