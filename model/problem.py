'''Problem model module'''


from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from . import BaseModel, model_context


class ProblemModel(BaseModel):
    '''Problem model.'''

    __tablename__ = 'problem'

    uid = Column('uid', Integer, primary_key=True)
    name = Column('name', String, index=True)
    revision = Column('revision', String)
    metadata = Column('metadata', JSONB)


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
    '''Get the problem by problem ID.

    Args:
        uid (int): problem ID.

    Returns:
        ProblemModel | None

    '''

    try:
        problem = await (ProblemModel.select()
            .where(ProblemModel.uid == uid)
            .first())
        return problem
    except:
        return None


@model_context
async def remove(uid, ctx):
    '''Remove the problem by problem ID.

    Args:
        uid (int): problem ID.

    Returns:
        True | False

    '''

    try:
        return await (ProblemModel.delete()
            .where(ProblemModel.uid == uid)
            .rowcount()) == 1
    except:
        return False


@model_context
async def list(start_uid=0, limit=None, ctx=None):
    '''List the problems.

    Args:
        start_uid (int): Lower bound of the problem ID.
        limit (int): The size limit.

    Returns:
        [ProblemModel]

    '''

    query = ProblemModel.select().where(ProblemModel.uid >= start_uid)
    if limit is not None:
        query = query.limit(limit)

    problems = []
    async for problem in query:
        problems.append(problem)

    return problems
