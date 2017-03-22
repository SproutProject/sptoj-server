'''ORM unittest'''


import tests
from model import *
from unittest import TestCase
from sqlalchemy import Table, Column, Integer, String, Enum
from sqlalchemy.dialects.postgresql import JSONB


class AModel(BaseModel):
    '''Test A Model.'''

    __tablename__ = 'A'

    uid = Column('zid', Integer, primary_key=True)
    data = Column('data', Integer)


class BModel(BaseModel):
    '''Test B Model.'''

    __tablename__ = 'B'

    uid = Column('yid', Integer, primary_key=True)
    name = Column('name', String)
    parent = Relation(AModel, back_populates='children')
    _data = Column('data', Integer)


class CModel(BaseModel):
    '''Test C Model.'''

    __tablename__ = 'C'

    uid = Column('xid', Integer, primary_key=True)
    name = Column('xname', String)
    aa = Relation(AModel)
    ba = Relation(BModel, back_populates='ca')
    bb = Relation(BModel, back_populates='cb')


class TestModel(TestCase):
    '''Model unittest.'''

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

        rowcount = (await BModel.select()
            .where(BModel.parent.data == 10)
            .execute(ctx.conn)).rowcount
        self.assertEqual(rowcount, 2)

        rowcount = (await BModel.select()
            .where(BModel.parent.uid == 1)
            .execute(ctx.conn)).rowcount
        self.assertEqual(rowcount, 2)

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

    @tests.async_test
    @model_context
    async def test_relation(self, ctx):
        '''Test relation.'''

        a = AModel(data=10)
        b1 = BModel(name='b1', parent=a, data=20)
        b2 = BModel(name='b2', parent=a, data=30)
        c = CModel(name='c', aa=a, ba=b1, bb=b2)
        c1 = CModel(name='c', aa=a, ba=b1, bb=b1)

        await a.save(ctx.conn)
        await b1.save(ctx.conn)
        await b2.save(ctx.conn)
        await c.save(ctx.conn)
        await c1.save(ctx.conn)

        rc = await (await CModel.select()
            .where(CModel.ba.data == 20)
            .where(CModel.bb.name == 'b2')
            .where(CModel.bb.parent.uid == 1)
            .execute(ctx.conn)).first()
        self.assertEqual(rc.name, 'c')
        self.assertEqual(rc.aa.data, 10)
        self.assertEqual(rc.ba.uid, 1)
        self.assertEqual(rc.bb.uid, 2)

        rowcount = (await CModel.select()
            .where(CModel.ba.parent.uid == 2)
            .execute(ctx.conn)).rowcount
        self.assertEqual(rowcount, 0)

        rowcount = (await b1.ca.execute(ctx.conn)).rowcount
        self.assertEqual(rowcount, 2)

        rc = await (await b2.cb.execute(ctx.conn)).first()
        self.assertEqual(rc.uid, 1)

    @tests.async_test
    @model_context
    async def test_delete(self, ctx):
        '''Test delete.'''

        a1 = AModel(data=10)
        a2 = AModel(data=20)
        b1 = BModel(name='b', parent=a1, data=20)
        b2 = BModel(name='b', parent=a2, data=20)
        b3 = BModel(name='b', parent=a2, data=20)

        await a1.save(ctx.conn)
        await a2.save(ctx.conn)
        await b1.save(ctx.conn)
        await b2.save(ctx.conn)
        await b3.save(ctx.conn)

        rowcount = (await BModel.delete()
            .where(BModel.parent.data == 20)
            .execute(ctx.conn)).rowcount
        self.assertEqual(rowcount, 2)

        rowcount = (await BModel.delete().execute(ctx.conn)).rowcount
        self.assertEqual(rowcount, 1)


class TestCommand(TestCase):
    '''Command unittest.'''

    @tests.async_test
    @model_context
    async def test_select(self, ctx):
        '''Test basic select.'''

        a = AModel(data=20)
        b = BModel(name='b', parent=a, data=20)

        await a.save(ctx.conn)
        await b.save(ctx.conn)

        query = select([BModel.name, BModel.data]).select_from(BModel)
        res = await (await query.execute(ctx.conn)).first()
        self.assertEqual(res, ('b', 20))

    @tests.async_test
    @model_context
    async def test_join_select(self, ctx):
        '''Test select on join.'''

        a = AModel(data=20)
        b = BModel(name='b', parent=a, data=20)

        await a.save(ctx.conn)
        await b.save(ctx.conn)

        query = (select([BModel.name, BModel.data])
            .select_from(BModel.join(AModel))
            .where(AModel.data == 20))
        res = await (await query.execute(ctx.conn)).first()
        self.assertEqual(res, ('b', 20))

    @tests.async_test
    @model_context
    async def test_select_foreign(self, ctx):
        '''Test select on foreign key.'''

        a = AModel(data=20)
        b = BModel(name='b', parent=a, data=20)

        await a.save(ctx.conn)
        await b.save(ctx.conn)

        query = (select([BModel.name, BModel.data])
            .select_from(BModel)
            .where(BModel.parent.uid == 1))
        res = await (await query.execute(ctx.conn)).first()
        self.assertEqual(res, ('b', 20))
