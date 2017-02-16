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
from sqlalchemy import ForeignKey, Column, Integer, Enum, func
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


async def update_rate_count(category, spec_problem_uid=None,
    update_problem=False, conn=None):
    '''Update rate count.
    
    Args:
        category (UserCategory): Category.
        spec_problem_uid (int, optional): Only update the specific problem ID.
    
    '''

    base_tbl = (select([
            ProblemModel.uid,
            func.coalesce(func.max(ProItemModel.deadline), 'infinity')
                .label('deadline')
        ])
        .select_from(ProItemModel.join(ProblemModel).join(ProSetModel))
        .where(ProSetModel.metadata['category'].astext.cast(Integer) ==
            int(category)))

    if spec_problem_uid is not None:
        base_tbl = base_tbl.where(ProblemModel.uid == spec_problem_uid)

    base_tbl = base_tbl.group_by(ProblemModel.uid).alias()

    count_tbl = (select([base_tbl.expr.c.uid, SubtaskModel.index]).
        select_from(base_tbl
            .join(ChallengeModel)
            .join(SubtaskModel)
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
            func.count().label('count'),
            TestWeightModel.weight
        ])
        .select_from(count_tbl.join(TestWeightModel))
        .group_by(count_tbl.expr.c.uid, count_tbl.expr.c.index,
            TestWeightModel.weight))

    async with conn.begin() as transcation:
        if update_problem:
            # Update tests and weights.

            await TestWeightModel.delete().execute(conn)

            query = await select([
                    ProblemModel.uid,
                    ProblemModel.metadata['test'].label('test')
                ])

            async for problem in await query.execute(conn):
                for index, test in enumerate(problem.test):
                    test_weight = TestWeightModel(problem_uid=problem.uid,
                        index=index, weight=test['weight'])
                        
                    await test_weight.save(conn)

        # Remove old data.
        query = (RateCountModel.delete()
            .where(RateCountModel.category == category))

        if spec_problem_uid is not None:
            query = query.where(RateCountModel.problem_uid == spec_problem_uid)
        
        await query.execute(conn)

        # Store accepted count.
        async for result in await count_query.execute(conn):
            problem_uid = result.problem_uid
            index = result.index
            count = result.count
            weight = result.weight

            assert count > 0

            score = int(500 * (float(weight) / 100.0) *
                (2**(28.0 / (count + 13.0))))

            rate_count = RateCountModel(category=category,
                problem_uid=problem_uid, index=index, count=count, score=score)

            await rate_count.save(conn)


async def update_rate_score(category, spec_problem_uid=None, conn=None):
    '''Update rate score.
    
    Args:
        category (UserCategory): Category.
        spec_problem_uid (int, optional): Only update the specific problem ID.
    
    '''

    base_tbl = (select([
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
            int(JudgeResult.STATUS_AC)))

    if spec_problem_uid is not None:
        base_tbl = base_tbl.where(ProblemModel.uid == spec_problem_uid)

    base_tbl = (base_tbl.group_by(UserModel.uid, ProblemModel.uid,
        SubtaskModel.index, ProItemModel.uid)
        .alias())

    score_query = (select([
            base_tbl.expr,
            ProItemModel.deadline,
            RateCountModel.score,
        ])
        .select_from(base_tbl
            .join(ProItemModel)
            .join(RateCountModel,
                (base_tbl.expr.c.problem_uid == RateCountModel.problem_uid) &
                (base_tbl.expr.c.index == RateCountModel.index),
                isouter=True)))

    async with conn.begin() as transcation:
        # Remove old data.
        query = (RateScoreModel.delete()
            .where(RateScoreModel.category == category))

        if spec_problem_uid is not None:
            query = query.where(RateScoreModel.problem_uid == spec_problem_uid)

        await query.execute(conn)

        async for result in await score_query.execute(conn):
            user_uid = result.user_uid
            problem_uid = result.problem_uid
            index = result.index
            deadline = result.deadline
            timestamp = result.timestamp
            score = result.score

            if score is None:
                score = 2000

            ratio = 1.0

            if deadline is not None:
                delta = (timestamp - deadline).total_seconds()
                if delta > 0:
                    ratio = 1.0 - min(1.0, (math.ceil(delta / 86400.0) * 0.15))

            score = int(score * ratio)

            if score > 0:
                rate_score = RateScoreModel(category=category,
                    user_uid=user_uid, problem_uid=problem_uid, index=index,
                    score=score)

                await rate_score.save(conn)


@model_context
async def refresh(ctx=None):
    '''Refresh everything.'''

    for category in UserCategory:
        if category == UserCategory.universe:
            continue

        await update_rate_count(category, conn=ctx.conn)
        await update_rate_score(category, conn=ctx.conn)


@model_context
async def change_category(old_category=None, new_category=None, ctx=None):
    '''Update when something's category changed.'''

    if old_category == UserCategory.universe:
        old_category = None

    if new_category == UserCategory.universe:
        new_category = None

    if old_category is not None:
        await update_rate_count(old_category, conn=ctx.conn)

    if new_category is not None:
        await update_rate_count(new_category, conn=ctx.conn)

    if old_category is not None:
        await update_rate_score(old_category, conn=ctx.conn)

    if new_category is not None:
        await update_rate_score(new_category, conn=ctx.conn)


@model_context
async def change_problem(problem_uid, ctx=None):
    '''Update when the problem changed.'''

    for category in UserCategory:
        if category == UserCategory.universe:
            continue

        await update_rate_count(category, problem_uid, conn=ctx.conn)
        await update_rate_score(category, problem_uid, conn=ctx.conn)
