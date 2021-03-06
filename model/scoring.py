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
from sqlalchemy import ForeignKey, Column, Integer, Enum, func, distinct
from . import BaseModel, model_context, select


class TestWeightModel(BaseModel):
    '''Test weight model.'''

    __tablename__ = 'test_weight'

    problem_uid = Column('problem_uid', Integer,
        ForeignKey(ProblemModel.uid, onupdate='CASCADE', ondelete='CASCADE'))
    index = Column('index', Integer, index=True)
    weight = Column('weight', Integer)
    score = Column('score', Integer)

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
    problem_updated=False, conn=None):
    '''Update rate count.

    Args:
        category (UserCategory): Category.
        spec_problem_uid (int) optional: Only update the specific problem ID.

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
            TestWeightModel.score
        ])
        .select_from(count_tbl.join(TestWeightModel,
            (count_tbl.expr.c.uid == TestWeightModel.problem_uid) &
            (count_tbl.expr.c.index == TestWeightModel.index)))
        .group_by(count_tbl.expr.c.uid, count_tbl.expr.c.index,
            TestWeightModel.score))

    async with conn.begin() as transcation:
        # Update all tests, weights and scores.
        if problem_updated:
            await TestWeightModel.delete().execute(conn)

            query = select([
                    ProblemModel.uid,
                    ProblemModel.metadata['test'].label('test'),
                    ProblemModel.metadata['score'].label('score')
                ])

            async for problem in await query.execute(conn):
                for index, test in enumerate(problem.test):
                    weight = test['weight']
                    test_weight = TestWeightModel(problem_uid=problem.uid,
                        index=index, weight=weight,
                        score=int(problem.score * float(weight) / 100.0))
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
            score = result.score

            assert count > 0

            score = score * (2**(28.0 / (count + 13.0)))

            rate_count = RateCountModel(category=category,
                problem_uid=problem_uid, index=index, count=count, score=score)

            await rate_count.save(conn)


async def update_rate_score(category, spec_problem_uid=None, conn=None):
    '''Update rate score.

    Args:
        category (UserCategory): Category.
        spec_problem_uid (int) optional: Only update the specific problem ID.

    '''

    base_tbl = (select([
            UserModel.uid.label('user_uid'),
            ProblemModel.uid.label('problem_uid'),
            SubtaskModel.index,
            func.max(ProItemModel.deadline).label('deadline'),
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
        SubtaskModel.index)
        .alias())

    score_query = (select([
            base_tbl.expr,
            TestWeightModel.score.label('max_score'),
            RateCountModel.score
        ])
        .select_from(base_tbl
            .join(TestWeightModel,
                (base_tbl.expr.c.problem_uid == TestWeightModel.problem_uid) &
                (base_tbl.expr.c.index == TestWeightModel.index))
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
                score = result.max_score * 4

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
    '''Update when something's category changed.

    Args:
        old_category (UserCategory): Old category.
        new_category (UserCategory): New category.

    '''

    if old_category == new_category:
        return

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
async def change_problem(problem_uid, problem_updated=False, ctx=None):
    '''Update the specific problem.

    Args:
        problem_uid (int): Problem ID.

    '''

    for category in UserCategory:
        if category == UserCategory.universe:
            continue

        await update_rate_count(category, problem_uid, problem_updated,
            conn=ctx.conn)
        await update_rate_score(category, problem_uid, conn=ctx.conn)


@model_context
async def get_problem_rate(category, problem_uid, ctx=None):
    '''Get problem rate for the specific category.

    Args:
        category (UserCategory): Category.
        problem_uid (int): Problem ID.

    Returns:
        [{ 'index' (int), 'count' (int), 'score' (int) }] | None

    '''

    async with ctx.conn.begin() as transcation:
        result = (await ProItemModel.select()
            .where(ProItemModel.problem.uid == problem_uid)
            .where(ProItemModel.parent.metadata['category']
                .astext.cast(Integer) == int(category))
            .limit(1)
            .execute(ctx.conn)).rowcount
        if result == 0:
            return None

        if category == UserCategory.algo:
            # Algo uses rate scoring.

            query = (TestWeightModel.select()
                .where(TestWeightModel.problem_uid == problem_uid)
                .order_by(TestWeightModel.index))

            results = {}
            async for test in await query.execute(ctx.conn):
                results[test.index] = {
                    'index': test.index,
                    'count': 0,
                    'score': test.score * 4
                }

            query = (RateCountModel.select()
                .where(RateCountModel.category == category)
                .where(RateCountModel.problem_uid == problem_uid))

            async for rate_count in await query.execute(ctx.conn):
                results[rate_count.index]['count'] = rate_count.count
                results[rate_count.index]['score'] = rate_count.score

            return sorted(results.values(), key=lambda x: x['index'])
        else:
            # Default statistic scoring.

            query = (TestWeightModel.select()
                .where(TestWeightModel.problem_uid == problem_uid))

            results = {}
            async for test in await query.execute(ctx.conn):
                results[test.index] = {
                    'index': test.index,
                    'count': 0,
                    'score': test.score
                }

            query = (select([
                    SubtaskModel.index,
                    func.count(distinct(UserModel.uid)).label('count')
                ])
                .select_from(ProblemModel
                    .join(ChallengeModel)
                    .join(UserModel)
                    .join(SubtaskModel))
                .where(ProblemModel.uid == problem_uid)
                .where(UserModel.category == category)
                .where(SubtaskModel.metadata['result'].astext.cast(Integer) ==
                    int(JudgeResult.STATUS_AC))
                .group_by(SubtaskModel.index))

            async for stat_count in await query.execute(ctx.conn):
                results[stat_count.index]['count'] = stat_count.count

            return sorted(results.values(), key=lambda x: x['index'])


@model_context
async def get_user_score(user, spec_problem_uid=None, spec_proset_uid=None,
    ctx=None):
    '''Get user score.

    Args:
        user (UserModel): User.

    Returns:
        Int | None

    '''

    if user.category == UserCategory.algo:
        # Algo uses rate scoring.
        base_tbl = (select([ProblemModel.uid])
            .select_from(ProItemModel
                .join(ProblemModel)
                .join(ProSetModel)))

        if spec_proset_uid is not None:
            base_tbl = base_tbl.where(ProSetModel.uid == spec_proset_uid)

        base_tbl = base_tbl.distinct(ProblemModel.uid).alias()

        query = (select([func.sum(RateScoreModel.score)], int)
            .select_from(RateScoreModel)
            .where(RateScoreModel.user_uid == user.uid)
            .where(RateScoreModel.problem_uid.in_(base_tbl.expr)))

        if spec_problem_uid is not None:
            query = query.where(RateScoreModel.problem_uid == spec_problem_uid)

        score = await (await query.execute(ctx.conn)).scalar()
        if score is None:
            score = 0

        return score
    else:
        # Default statistic scoring.

        # TODO optimize the queries.

        base_tbl = (select([
                TestWeightModel.problem_uid,
                TestWeightModel.index,
                TestWeightModel.score
            ])
            .select_from(ProItemModel
                .join(ProblemModel)
                .join(ProSetModel)
                .join(TestWeightModel,
                    ProblemModel.uid == TestWeightModel.problem_uid))
            .where(ProSetModel.metadata['category'].astext.cast(Integer) ==
                int(user.category))
            .distinct(TestWeightModel.problem_uid, TestWeightModel.index,
                TestWeightModel.score))

        if spec_proset_uid is not None:
            base_tbl = base_tbl.where(ProSetModel.uid == spec_proset_uid)

        base_tbl = base_tbl.alias()

        score_tbl = (select([base_tbl.expr.c.score], int)
            .select_from(ChallengeModel
                .join(UserModel)
                .join(ProblemModel)
                .join(SubtaskModel)
                .join(base_tbl,
                    (ProblemModel.uid == base_tbl.expr.c.problem_uid) &
                    (SubtaskModel.index == base_tbl.expr.c.index)))
            .where(UserModel.uid == user.uid)
            .where(SubtaskModel.metadata['result'].astext.cast(Integer) ==
                int(JudgeResult.STATUS_AC)))

        if spec_problem_uid is not None:
            score_tbl = score_tbl.where(
                ProblemModel.problem_uid == spec_problem_uid)

        score_tbl = score_tbl.distinct(base_tbl.expr.c.problem_uid,
            base_tbl.expr.c.index, base_tbl.expr.c.score).alias()

        score = await (await select([func.sum(score_tbl.expr.c.score)], int)
            .select_from(score_tbl)
            .execute(ctx.conn)).scalar()
        if score is None:
            score = 0

        return score
