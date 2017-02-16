'''Scoring model module'''


import math
import asyncio
import aiopg.sa
import config
import sqlalchemy as sa
from model.user import UserModel, UserCategory
from model.problem import ProblemModel
from model.proset import ProSetModel, ProItemModel
from model.challenge import ChallengeModel, SubtaskModel
from model.challenge import JudgeState, JudgeResult
from sqlalchemy import ForeignKey, Column, Integer, Enum, func, text
from . import BaseModel, model_context, select


class TestWeightModel(BaseModel):
    '''Test weight model.'''

    __tablename__ = 'test_weight'

    problem_uid = Column('problem_uid', Integer,
        ForeignKey(ProblemModel.uid, onupdate='CASCADE', ondelete='CASCADE'))
    index = Column('index', Integer, index=True)
    weight = Column('weight', Integer)

    __primarykey__ = [problem_uid, index]


class RateCountModel(BaseModel):
    '''Rate accepted count model.'''

    __tablename__ = 'rate_count'

    category = Column('category', Enum(UserCategory))
    problem_uid = Column('problem_uid', Integer,
        ForeignKey(ProblemModel.uid, onupdate='CASCADE', ondelete='CASCADE'))
    index = Column('index', Integer, index=True)
    count = Column('count', Integer)
    score = Column('score', Integer)

    __primarykey__ = [category, problem_uid, index]


class RateScoreModel(BaseModel):
    '''Rate accepted count model.'''

    __tablename__ = 'rate_score'

    category = Column('category', Enum(UserCategory))
    user_uid = Column('user_uid', Integer,
        ForeignKey(UserModel.uid, onupdate='CASCADE', ondelete='CASCADE'))
    problem_uid = Column('problem_uid', Integer,
        ForeignKey(ProblemModel.uid, onupdate='CASCADE', ondelete='CASCADE'))
    index = Column('index', Integer, index=True)
    score = Column('score', Integer)

    __primarykey__ = [category, user_uid, problem_uid, index]


async def async_lambda():
    '''Async lambda function.'''

    engine = await aiopg.sa.create_engine(config.DB_URL)
    async with engine.acquire() as conn:
        category = UserCategory.clang

        # Update tests and weights.
        problems = (await select([ProblemModel.uid,
                ProblemModel.metadata['test'].label('test')]).execute(conn))
        async for problem in problems:
            for index, test in enumerate(problem.test):
                await TestWeightModel(problem_uid=problem.uid, index=index,
                    weight=test['weight']).save(conn)

        base_tbl = (select([
                ProblemModel.uid,
                func.coalesce(func.max(ProItemModel.deadline), 'infinity')
                    .label('deadline')
            ])
            .select_from(ProItemModel.join(ProblemModel).join(ProSetModel))
            .where(ProSetModel.metadata['category'].astext.cast(Integer) ==
                int(category))
            .group_by(ProblemModel.uid)
            .alias())

        count_tbl = (select([base_tbl.expr.c.uid, SubtaskModel.index]).
            select_from(base_tbl.join(ChallengeModel).join(SubtaskModel)
                .join(UserModel))
            .where(UserModel.category == category)
            .where(ChallengeModel.state == JudgeState.done)
            .where(ChallengeModel.timestamp <= base_tbl.expr.c.deadline)
            .where(SubtaskModel.metadata['result'].astext.cast(Integer) ==
                int(JudgeResult.STATUS_AC))
            .distinct(UserModel.uid, base_tbl.expr.c.uid, SubtaskModel.index)
            .alias())

        count_query = (select([
                count_tbl.expr.c.uid.label('problem_uid'),
                count_tbl.expr.c.index,
                func.count().label('count')
            ])
            .select_from(count_tbl)
            .group_by(count_tbl.expr.c.uid, count_tbl.expr.c.index))

        async with conn.begin() as transcation:
            # Get all related tests.
            proidxs = {}
            async for result in await proidx_query.execute(conn):
                proidxs[(result.problem_uid, result.index)] = result.weight

            # Store accepted count.
            async for result in await count_query.execute(conn):
                problem_uid = result.problem_uid
                index = result.index
                count = result.count
                weight = proidxs[(problem_uid, index)]

                assert count > 0

                score = int(500 * (float(weight) / 100.0) *
                    (2**(28.0 / (count + 13.0))))

                rate_count = RateCountModel(category=category,
                    problem_uid=problem_uid, index=index, count=count,
                    score=score)

                await rate_count.save(conn)
                del proidxs[(problem_uid, index)]

            # Clean empty tests.
            for problem_uid, index in proidxs.keys():
                await (RateCountModel.delete()
                    .where((RateCountModel.category == category) &
                        (RateCountModel.problem_uid == problem_uid) &
                        (RateCountModel.index == index))
                    .execute(conn))

def calc_rate(count, deadline, timestamp):
    pass

async def async_user():

    engine = await aiopg.sa.create_engine(config.DB_URL)
    async with engine.acquire() as conn:
        category = UserCategory.clang

        tbl = (select([
                UserModel.uid.label('user_uid'),
                ProblemModel.uid.label('problem_uid'),
                SubtaskModel.index,
                ProItemModel.uid.label('proitem_uid'),
                func.min(ChallengeModel.timestamp).label('timestamp')
            ])
            .select_from(UserModel
                .join(ChallengeModel)
                .join(SubtaskModel)
                .join(ProblemModel)
                .join(ProItemModel)
                .join(ProSetModel))
            .where(UserModel.category == category)
            .where(ProSetModel.metadata['category'].astext.cast(Integer) ==
                int(category))
            .where(ChallengeModel.state == JudgeState.done)
            .where(SubtaskModel.metadata['result'].astext.cast(Integer) ==
                int(JudgeResult.STATUS_AC))
            .group_by(UserModel.uid, ProblemModel.uid, SubtaskModel.index,
                ProItemModel.uid)
            .alias())

        query = (select([
                tbl.expr,
                ProItemModel.deadline,
                RateCountModel.score,
            ])
            .select_from(tbl
                .join(ProItemModel)
                .join(RateCountModel,
                    (tbl.expr.c.problem_uid == RateCountModel.problem_uid) &
                    (tbl.expr.c.index == RateCountModel.index),
                    isouter=True)))

        async for result in await query.execute(conn):
            user_uid = result.user_uid
            problem_uid = result.problem_uid
            index = result.index
            deadline = result.deadline
            timestamp = result.timestamp
            score = result.score

            if score is None:
                score = 2000

            ratio = 1.0

            delta = (timestamp - deadline).total_seconds()
            if delta > 0:
                ratio = 1.0 - min(1.0, (math.ceil(delta / 86400.0) * 0.15))

            score = int(score * ratio)

            await RateScoreModel(category=category, user_uid=user_uid,
                problem_uid=problem_uid, index=index, score=score).save(conn)

        # Clean empty tests.
        for problem_uid, index in proidxs.keys():
            await (RateCountModel.delete()
                .where((RateCountModel.category == category) &
                    (RateCountModel.problem_uid == problem_uid) &
                    (RateCountModel.index == index))
                .execute(conn))

import model

model.create_schemas(config.DB_URL)

loop = asyncio.get_event_loop()
loop.run_until_complete(async_lambda())
loop.run_until_complete(async_user())
