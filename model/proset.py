'''ProSet model module'''


from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from model.problem import ProblemModel
from . import BaseModel, Relation, model_context


class ProSetModel(BaseModel):
    '''ProSet model.'''

    __tablename__ = 'proset'

    uid = Column('uid', Integer, primary_key=True)
    name = Column('name', String, index=True)
    hidden = Column('hidden', Boolean, index=True)

    @model_context
    async def update(self, ctx):
        '''Save the changes.

        Returns:
            True | False

        '''

        try:
            await self.save(ctx.conn)
            return True
        except:
            return False

    @model_context
    async def remove(self, ctx):
        '''Remove the problem set.

        Args:
            proset (ProSetModel): Problem set.

        Returns:
            True | False

        '''

        try:
            return (await ProSetModel.delete()
                .where(ProSetModel.uid == self.uid)
                .execute(ctx.conn)).rowcount == 1
        except:
            return False

    @model_context
    async def add(self, problem, hidden=True, deadline=None, metadata={},
        ctx=None):
        '''Add a item to the problem set.

        Args:
            problem (Problem): The problem.

        Returns:
            ProItem | None

        '''

        try:
            proitem = ProItemModel(parent=self, problem=problem, hidden=hidden,
                deadline=deadline, metadata=metadata)
            await proitem.save(ctx.conn)
            return proitem
        except:
            return None

    @model_context
    async def get(self, uid, ctx):
        '''Get the item by the item ID.

        Args:
            uid (int): Item ID.

        Returns:
            ProItem | None

        '''

        try:
            proitem = await (await ProItemModel.select()
                .where((ProItemModel.uid == uid) &
                    (ProItemModel.parent.uid == self.uid))
                .execute(ctx.conn)).first()
            return proitem
        except:
            return None

    @model_context
    async def list(self, start_uid=0, limit=None, hidden=False, ctx=None):
        '''List the items.

        Args:
            start_uid (int): Lower bound of the item ID.
            limit (int): The size limit.
            hidden (bool): Show hidden or not.

        Returns:
            [ProItem] | None

        '''

        query = self.items.where(ProItemModel.uid >= start_uid)

        if not hidden:
            query = query.where(ProItemModel.hidden == False)

        if limit is not None:
            query = query.limit(limit)

        query = query.order_by(ProItemModel.uid)

        try:
            proitems = []
            async for proitem in (await query.execute(ctx.conn)):
                proitems.append(proitem)

            return proitems
        except:
            return None


class ProItemModel(BaseModel):
    '''ProItem model.'''

    __tablename__ = 'proitem'

    uid = Column('uid', Integer, primary_key=True)
    hidden = Column('hidden', Boolean, index=True)
    deadline = Column('deadline', DateTime(timezone=True), index=True)
    metadata = Column('metadata', JSONB)
    _parent = Relation(ProSetModel, back_populates='items')
    _problem = Relation(ProblemModel)

    @model_context
    async def update(self, ctx):
        '''Save the changes.

        Returns:
            True | False

        '''

        try:
            await self.save(ctx.conn)
            return True
        except:
            return False

    @model_context
    async def remove(self, ctx):
        '''Remove the item from the problem set.

        Args:
            proitem (ProItem): Problem item.

        Returns:
            True | False

        '''

        try:
            return (await ProItemModel.delete()
                .where(ProItemModel.uid == self.uid)
                .execute(ctx.conn)).rowcount == 1
        except:
            return None


@model_context
async def create(name, hidden, ctx):
    '''Create a problem set.

    Args:
        name (string): Name.
        hidden (bool): Is hidden or not.

    Returns:
        ProSetModel | None

    '''

    try:
        proset = ProSetModel(name=name, hidden=hidden)
        await proset.save(ctx.conn)
        return proset
    except:
        return None


@model_context
async def get(uid, ctx):
    '''Get the problem set by problem set ID.

    Args:
        uid (int): Problem set ID.

    Returns:
        ProblemModel | None

    '''

    try:
        proset = await (await ProSetModel.select()
            .where(ProSetModel.uid == uid)
            .execute(ctx.conn)).first()
        return proset
    except:
        return None


@model_context
async def get_list(start_uid=0, limit=None, hidden=False, ctx=None):
    '''List the problem sets.

    Args:
        start_uid (int): Lower bound of the problem set ID.
        limit (int): The size limit.
        hidden (bool): Show hidden or not.

    Returns:
        [ProSetModel] | None

    '''

    query = ProSetModel.select().where(ProSetModel.uid >= start_uid)

    if not hidden:
        query = query.where(ProSetModel.hidden == False)

    if limit is not None:
        query = query.limit(limit)

    query = query.order_by(ProSetModel.uid)

    try:
        prosets = []
        async for proset in (await query.execute(ctx.conn)):
            prosets.append(proset)

        return prosets
    except:
        return None
