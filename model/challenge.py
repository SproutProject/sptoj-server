'''Challenge model module'''


import enum
import model.scoring
from datetime import datetime, timezone
from sqlalchemy import Table, Column,Integer, String, Enum, DateTime
from sqlalchemy.sql.expression import func, text
from sqlalchemy.dialects.postgresql import JSONB
from model.user import UserModel
from model.proset import ProSetModel, ProItemModel
from model.problem import ProblemModel
from . import BaseModel, Relation, model_context, select


@enum.unique
class JudgeState(enum.IntEnum):
    pending = 0
    running = 1
    done = 2


@enum.unique
class JudgeResult(enum.IntEnum):
    STATUS_NONE = 0
    STATUS_AC = 1
    STATUS_WA = 2
    STATUS_RE = 3
    STATUS_TLE = 4
    STATUS_MLE = 5
    STATUS_CE = 6
    STATUS_ERR = 7


class ChallengeModel(BaseModel):
    '''Challenge model.'''

    __tablename__ = 'challenge'

    uid = Column('uid', Integer, primary_key=True)
    _revision = Column('revision', String)
    _state = Column('state', Enum(JudgeState))
    timestamp = Column('timestamp', DateTime(timezone=True), index=True)
    metadata = Column('metadata', JSONB)
    _submitter = Relation(UserModel, back_populates="challenges")
    _problem = Relation(ProblemModel, back_populates="challenges")

    @model_context
    async def reset(self, ctx):
        '''Reset the challenge.

        Returns:
            True | False

        '''
        try:
            async with ctx.conn.begin() as transaction:
                self._revision = self.problem.revision
                self._state = JudgeState.pending
                self._metadata = {}
                await self.save(ctx.conn)

                # TODO Stronger ORM delete.
                async for subtask in (await self.subtasks.execute(ctx.conn)):
                    await (SubtaskModel.delete()
                        .where(SubtaskModel.uid == subtask.uid)
                        .execute(ctx.conn))

                for idx, test in enumerate(self.problem.metadata['test']):
                    subtask = SubtaskModel(index=idx, state=JudgeState.pending,
                        metadata={}, challenge=self)
                    await subtask.save(ctx.conn)

                return True
        except:
            raise
            return False

    @model_context
    async def update_subtask(self, index, state, metadata=None, ctx=None):
        '''Update the subtask.

        Args:
            index (int): Subtask index.
            state (JudgeState): Subtask state.
            metadata (object): Subtask metadata.

        Returns:
            True | False

        '''

        try:
            async with ctx.conn.begin() as transaction:
                # Update subtask.
                subtask = (await (await self.subtasks
                    .where(SubtaskModel.index == index)
                    .execute(ctx.conn)).first())

                subtask._state = state

                if metadata is not None:
                    subtask.metadata['memory'] = int(metadata['memory'])
                    subtask.metadata['runtime'] = int(metadata['runtime'])
                    subtask.metadata['result'] = int(metadata['result'])
                    subtask.metadata['verdict'] = [str(verdict)
                        for verdict in metadata['verdict']]

                await subtask.save(ctx.conn)

                # Get state summary.
                table = self.subtasks.alias().expr
                state = (await (await select([func.min(table.c.state)], int)
                    .select_from(table)
                    .execute(ctx.conn)).scalar())

                self._state = state

                # Update metadata.
                if self.state == JudgeState.done:
                    total_mem = 0
                    total_runtime = 0
                    result = 0
                    verdict = ''

                    for subtask in await self.list():
                        total_mem += subtask.metadata['memory']
                        total_runtime += subtask.metadata['runtime']
                        result = max(result, subtask.metadata['result'])

                        # Get compile error information.
                        if result == JudgeResult.STATUS_CE and verdict == '':
                            # All compile error verdicts are same.
                            verdict = subtask.metadata['verdict'][0]

                    self.metadata = {
                        'memory': total_mem,
                        'runtime': total_runtime,
                        'result': result,
                        'verdict': verdict,
                    }

                await self.save(ctx.conn)

            if self.state == JudgeState.done:
                await model.scoring.change_problem(self.problem.uid)

            return True
        except:
            return False

    @model_context
    async def remove(self, ctx):
        '''Remove a challenge.

        Args:
            challenge (ChallengeModel): Challenge.

        Returns:
            True | False

        '''

        try:
            old_state = self.state
            problem_uid = self.problem.uid

            result =  (await ChallengeModel.delete()
                .where(ChallengeModel.uid == self.uid)
                .execute(ctx.conn)).rowcount
            if result == 0:
                return False

            if old_state == JudgeState.done:
                await model.scoring.change_problem(problem_uid)

            return True
        except:
            return False

    @model_context
    async def list(self, ctx):
        '''List subtasks.

        Returns:
            [SubtaskModel] | None

        '''

        query = self.subtasks.order_by(SubtaskModel.index)

        try:
            subtasks = []
            async for subtask in (await query.execute(ctx.conn)):
                subtasks.append(subtask)

            return subtasks
        except:
            return None

    @model_context
    async def is_hidden(self, ctx):
        '''Check if the challenge is hidden.

        Returns:
            True | False

        '''

        problem_uid = self.problem.uid

        query = (ProItemModel.select()
            .where((ProItemModel.problem.uid == problem_uid) &
                (ProItemModel.hidden == False) &
                (ProItemModel.parent.hidden == False)))
        return (await query.execute(ctx.conn)).rowcount == 0


class SubtaskModel(BaseModel):
    '''Subtask model.'''

    __tablename__ = 'subtask'

    uid = Column('uid', Integer, primary_key=True)
    _index = Column('index', Integer, index=True)
    _state = Column('state', Enum(JudgeState))
    metadata = Column('metadata', JSONB)
    _challenge = Relation(ChallengeModel, back_populates="subtasks")


@model_context
async def create(submitter, problem, ctx):
    '''Create a challenge.

    Args:
        submitter (UserModel): Submitter.
        problem (ProblemModel): Problem.

    Returns:
        ChallengeModel | None

    '''

    try:
        async with ctx.conn.begin():
            challenge = ChallengeModel(
                revision=problem.revision,
                state=JudgeState.pending,
                timestamp=datetime.now(tz=timezone.utc),
                metadata={},
                submitter=submitter,
                problem=problem)
            await challenge.save(ctx.conn)

            for idx, test in enumerate(problem.metadata['test']):
                subtask = SubtaskModel(index=idx, state=JudgeState.pending,
                    metadata={}, challenge=challenge)
                await subtask.save(ctx.conn)

        return challenge
    except:
        return None


@model_context
async def get(uid, ctx):
    '''Get the challenge by challenge ID.

    Args:
        uid (int): challenge ID.

    Returns:
        ChallengeModel | None

    '''

    try:
        return await (await ChallengeModel.select()
            .where(ChallengeModel.uid == uid)
            .execute(ctx.conn)).first()
    except:
        return None


@model_context
async def get_list(offset=0, limit=None, user_uid=None, problem_uid=None,
    state=None, result=None, ctx=None):
    '''List the challenges.

    Args:
        offset (int): The offset.
        limit (int): The size limit.
        user_uid (int): User ID filter.
        problem_uid (int): Problem ID filter.
        state (JudgeState): State filter.
        result (JudgeResult): Result filter.

    Returns:
        { 'count' (int), 'data' ([ChallengeModel]) } | None

    '''

    query = ChallengeModel.select()

    if user_uid is not None:
        query = query.where(ChallengeModel.submitter.uid == user_uid)

    if problem_uid is not None:
        query = query.where(ChallengeModel.problem.uid == problem_uid)

    if state is not None:
        query = query.where(ChallengeModel.state == state)

    if result is not None:
        query = query.where(ChallengeModel.metadata['result']
            .astext.cast(Integer) == result)

    query = query.order_by(ChallengeModel.uid).offset(offset)

    try:
        count = (await query.execute(ctx.conn)).rowcount

        if limit is not None:
            query = query.limit(limit)

        challenges = []
        async for challenge in (await query.execute(ctx.conn)):
            challenges.append(challenge)

        return { 'count': count, 'data': challenges }
    except:
        return None


@model_context
async def stat_result(user_uids, problem_uids, ctx=None):
    '''Statistic results.

    Args:
        user_uids ([int]): Included User IDs.
        problem_uids ([int]): Included Problem IDs.

    Returns:
        {(user_uid (int), problem_uid (int)): result (int), ...} | None

    '''

    if len(user_uids) == 0 or len(problem_uids) == 0:
        return {}

    query = (select([
            UserModel.uid.label('user_uid'),
            ProblemModel.uid.label('problem_uid'),
            func.min(ChallengeModel.metadata['result']
                .astext.cast(Integer)).label('result')
        ])
        .select_from(ChallengeModel.join(UserModel).join(ProblemModel))
        .where(ChallengeModel.state == JudgeState.done)
        .where(UserModel.uid.in_(user_uids))
        .where(ProblemModel.uid.in_(problem_uids))
        .group_by(UserModel.uid, ProblemModel.uid))

    try:
        ret_map = {}
        async for result in await query.execute(ctx.conn):
            ret_map[(result.user_uid, result.problem_uid)] = result.result

        return ret_map
    except:
        return None
