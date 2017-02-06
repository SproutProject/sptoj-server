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
    metadata = Column('metadata', JSONB)
    _submitter = Relation(UserModel, back_populates="challenges")
    _problem = Relation(ProblemModel, back_populates="challenges")


class SubtaskModel(BaseModel):
    '''Subtask model.'''

    __tablename__ = 'subtask'

    uid = Column('uid', Integer, primary_key=True)
    state = Column('state', Enum(JudgeState))
    metadata = Column('metadata', JSONB)
    challenge = Relation(ChallengeModel, back_populates="subtasks")


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
        challenge = ChallengeModel(_revision=problem.revision,
            _state=JudgeState.pending, metadata={}, _submitter=submitter,
            _problem=problem)
        await challenge.save(ctx.conn)
        return challenge
    except:
        raise
        return None
