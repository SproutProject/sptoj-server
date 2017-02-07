'''Challenge model module'''


import enum
from sqlalchemy import Table, Column,Integer, String, Enum
from sqlalchemy.dialects.postgresql import JSONB
from model.user import UserModel
from model.problem import ProblemModel
from . import BaseModel, Relation, model_context


@enum.unique
class JudgeState(enum.IntEnum):
    pending = 0
    running = 1
    done = 2


class ChallengeModel(BaseModel):
    '''Challenge model.'''

    __tablename__ = 'challenge'

    uid = Column('uid', Integer, primary_key=True)
    _revision = Column('revision', String)
    _state = Column('state', Enum(JudgeState))
    _submitter = Relation(UserModel, back_populates="challenges")
    _problem = Relation(ProblemModel, back_populates="challenges")


class SubtaskModel(BaseModel):
    '''Subtask model.'''

    __tablename__ = 'subtask'

    uid = Column('uid', Integer, primary_key=True)
    _state = Column('state', Enum(JudgeState))
    metadata = Column('metadata', JSONB)
    _challenge = Relation(ChallengeModel, back_populates="subtasks")


@model_context
async def create(submitter, problem, ctx):
    '''Create a challenge.

    Args:
        submitter (UserModel): The submitter.
        problem (ProblemModel): The problem.

    Returns:
        ChallengeModel | None

    '''

    try:
        tests = problem.metadata['test']

        async with ctx.conn.begin():
            challenge = ChallengeModel(revision=problem.revision,
                state=JudgeState.pending, submitter=submitter, problem=problem)
            await challenge.save(ctx.conn)

            for test in tests:
                subtask = SubtaskModel(state=JudgeState.pending, metadata=test,
                    challenge=challenge)
                await subtask.save(ctx.conn)

        return challenge
    except:
        raise
        return None
