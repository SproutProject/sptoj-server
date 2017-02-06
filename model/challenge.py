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
    revision = Column('revision', String)
    state = Column('state', Enum(JudgeState))
    metadata = Column('metadata', JSONB)
    challenger = Relation(UserModel, back_populates="challenges")
    problem = Relation(ProblemModel, back_populates="challenges")


class SubtaskModel(BaseModel):
    '''Subtask model.'''

    __tablename__ = 'subtask'

    uid = Column('uid', Integer, primary_key=True)
    state = Column('state', Enum(JudgeState))
    metadata = Column('metadata', JSONB)
    challenge = Relation(ChallengeModel, back_populates="subtasks")
