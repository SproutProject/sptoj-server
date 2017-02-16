'''Problem model module'''


import model.scoring
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from . import BaseModel, model_context


class ProblemModel(BaseModel):
    '''Problem model.'''

    __tablename__ = 'problem'

    uid = Column('uid', Integer, primary_key=True)
    _name = Column('name', String, index=True)
    revision = Column('revision', String)
    metadata = Column('metadata', JSONB)

    @model_context
    async def remove(self, ctx):
        '''Remove the problem.

        Returns:
            True | False

        '''

        try:
            problem_uid = self.uid

            result = (await ProblemModel.delete()
                .where(ProblemModel.uid == problem_uid)
                .execute(ctx.conn)).rowcount
            if result == 0:
                return False

            await model.scoring.change_problem(problem_uid, True)

            return True
        except:
            return False


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
        # TODO Format the problem metadata.

        metadata['name'] = str(metadata['name'])
        metadata['score'] = int(metadata['score'])

        tests = []
        for idx, test in enumerate(metadata['test']):
            tests.append({
                'weight': int(test['weight']),
                'data': [int(dataidx) for dataidx in test['data']],
            })
        metadata['test'] = tests

        problem = ProblemModel(uid=uid, name=metadata['name'],
            revision=revision, metadata=metadata)
        await problem.save(ctx.conn)

        await model.scoring.change_problem(problem.uid, True)

        return problem
    except:
        raise
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
        return await (await ProblemModel.select()
            .where(ProblemModel.uid == uid)
            .execute(ctx.conn)).first()
    except:
        return None


@model_context
async def get_list(start_uid=0, limit=None, ctx=None):
    '''List the problems.

    Args:
        start_uid (int): Lower bound of the problem ID.
        limit (int): The size limit.

    Returns:
        [ProblemModel] | None

    '''

    query = ProblemModel.select().where(ProblemModel.uid >= start_uid)

    if limit is not None:
        query = query.limit(limit)

    try:
        problems = []
        async for problem in (await query.execute(ctx.conn)):
            problems.append(problem)

        return problems
    except:
        return None
