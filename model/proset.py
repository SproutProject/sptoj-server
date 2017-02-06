'''ProSet model module'''


from sqlalchemy import Table, Column, Integer, String, Boolean
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
    async def add(self, problem, ctx):
        '''Add a item to the problem set.

        Args:
            problem (Problem): The problem.

        Returns:
            ProItem | None

        '''

        try:
            proitem = ProItemModel(parent=self, problem=problem)
            await proitem.save(ctx.conn)
            return proitem
        except:
            return None

    @model_context
    async def remove(self, proitem, ctx):
        '''Remove the item from the problem set.

        Args:
            proitem (ProItem): The item.

        Returns:
            True | False

        '''

        try:
            return await (ProItemModel.delete()
                .where(ProItemModel.uid == proitem.uid)
                .rowcount()) == 1
        except:
            return None

    @model_context
    async def list(self, start_uid=0, limit=None, ctx=None):
        '''List the problems.

        Args:
            start_uid (int): Lower bound of the item ID.
            limit (int): The size limit.

        Returns:
            [ProItem]

        '''

        query = self.items.where(ProItemModel.uid >= start_uid)
        if limit is not None:
            query = query.limit(limit)

        proitems = []
        async for proitem in query:
            proitems.append(proitem)

        return proitems


class ProItemModel(BaseModel):
    '''ProItem model.'''

    __tablename__ = 'proitem'

    uid = Column('uid', Integer, primary_key=True)
    parent = Relation(ProSetModel, back_populates='items')
    problem = Relation(ProblemModel)

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
async def create(name, hidden, ctx):
    '''Create a problem set.

    Args:
        name (string): Problem set name.
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
        uid (int): problem set ID.

    Returns:
        ProblemModel | None

    '''

    try:
        proset = await (ProSetModel.select()
            .where(ProSetModel.uid == uid)
            .first())
        return proset
    except:
        return None


@model_context
async def remove(proset, ctx):
    '''Remove the problem set.

    Args:
        proset (ProSetModel): The problem set.

    Returns:
        True | False

    '''

    try:
        return await (ProSetModel.delete()
            .where(ProSetModel.uid == proset.uid)
            .rowcount()) == 1
    except:
        return False
