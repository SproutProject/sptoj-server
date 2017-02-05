'''Problem model module'''


from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from . import BaseModel, Relation, model_context


class ProblemModel(BaseModel):
    '''Problem model.'''

    __tablename__ = 'problem'

    uid = Column('uid', Integer, primary_key=True)
    name = Column('name', String, index=True)
    revision = Column('revision', String)
    metadata = Column('metadata', JSONB)


class ProSetModel(BaseModel):
    '''ProSet model.'''

    __tablename__ = 'proset'

    uid = Column('uid', Integer, primary_key=True)
    name = Column('name', String, index=True)


class ProItemModel(BaseModel):
    '''ProItem model.'''

    __tablename__ = 'proitem'

    uid = Column('uid', Integer, primary_key=True)

    parent = Relation(ProSetModel, back_populates='items')
    problem = Relation(ProblemModel)


@model_context
async def create(uid, revision, metadata, ctx):
    '''Create or update a problem.

    Args:
        uid (int): Problem ID.
        revision (string): Problem revision.
        metadata (object): Problem metadata.

    Return:
        ProblemModel | None

    '''

    try:
        name = metadata['name']
        problem = ProblemModel(
            uid=uid, name=name, revision=revision, metadata=metadata)
        await problem.save(ctx.conn)
        return problem
    except:
        return None


@model_context
async def get(uid, ctx):
    '''Get the problem from Problem ID.

    Args:
        uid (int): Problem ID.

    Returns:
        ProblemModel | None

    '''

    try:
        problem = await (await ProblemModel.select()
            .where(ProblemModel.uid == uid)
            .execute(ctx.conn)).first()
        return problem
    except:
        return None


@model_context
async def remove(uid, ctx):
    '''Remove the problem from Problem ID.

    Args:
        uid (int): Problem ID.

    Returns:
        True | False

    '''

    try:
        return (await ProblemModel.delete()
            .where(ProblemModel.uid == uid)
            .execute(ctx.conn)).rowcount == 1
    except:
        return False


@model_context
async def list(start_uid=0, limit=None, ctx=None):
    '''List the problems.

    Args:
        start_uid (int): Lower bound of the problem ID.
        limit (int): The size limit.

    Returns:
        [PorblemModel]

    '''

    query = ProblemModel.select().where(ProblemModel.uid >= start_uid)
    if limit is not None:
        query = query.limit(limit)

    problems = []
    async for problem in (await query.execute(ctx.conn)):
        problems.append(problem)

    return problems


@model_context
async def test(ctx):
    problem = await create(1000, 'deadbeef', { 'name': 'foo' })
    proset = ProSetModel(name='square')
    await proset.save(ctx.conn)
    proitem = ProItemModel(parent=proset)
    proitem.problem = problem
    await proitem.save(ctx.conn)

    results = await ProItemModel.select().where(ProItemModel.uid == proitem.uid).execute(ctx.conn)
    proitem = await results.first()
    print(proitem.uid, proitem.problem, proitem.parent)

    results = await proitem.parent.items.execute(ctx.conn)
    async for proitem in results:
        print(proitem.uid)
