'''Proset view module'''


import config
import model.challenge
import view.proset
import os
import json
import enum
import asyncio
import aiohttp
from datetime import datetime
from model.user import UserLevel
from model.challenge import JudgeState
from .interface import *
from . import APIHandler, Attribute, Interface, worker_context


@worker_context
async def emit_challenge(challenge, code_path):
    '''Emit the challenge and update the results.

    Args:
        challenge (ChallengeModel): Challenge.
        code_path (string): File path of the code.

    '''

    problem = challenge.problem
    code_path = os.path.abspath(code_path)
    res_path = os.path.abspath(
        os.path.join(config.PROBLEM_DIR, '{}/res'.format(problem.uid)))

    tests = []
    for idx, test in enumerate(problem.metadata['test']):
        tests.append({
            'test_idx': idx,
            'timelimit': problem.metadata['timelimit'],
            'memlimit': problem.metadata['memlimit'] * 1024,
            'metadata': { 'data': test['data'] }
        })
        await challenge.update_subtask(idx, JudgeState.running)

    data = {
        'chal_id': challenge.uid,
        'code_path': code_path,
        'res_path': res_path,
        'comp_type': problem.metadata['compile'],
        'check_type': problem.metadata['check'],
        'metadata': {},
        'test': tests,
    }

    api_url = config.JUDGE_URL + '/reqjudge'

    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, data=json.dumps(data)) as response:
            results = (await response.json())['result']
            for result in results:
                await challenge.update_subtask(result['test_idx'],
                    JudgeState.done, {
                        'result': result['state'],
                        'runtime': result['runtime'],
                        'memory': result['peakmem'] / 1024,
                        'verdict': result['verdict'],
                    })


class GetHandler(APIHandler):
    '''Get challenge information handler.'''

    async def process(self, uid, data=None):
        '''Process the request.

        Args:
            uid (int): Challenge ID.
            data (object): {}

        Returns:
            ChallengeInterface | 'Error'

        '''

        uid = int(uid)

        challenge = await model.challenge.get(uid)
        if challenge is None:
            return 'Error'

        if await view.proset.is_problem_hidden(self.user,
                challenge.problem.uid):
            return 'Error'

        subtasks = await challenge.list()
        if subtasks is None:
            return 'Error'

        viewall = False
        if self.user is not None and (
                self.user.uid == challenge.submitter.uid or
                self.user.level <= UserLevel.kernel):
            viewall = True

        if viewall:
            loop = asyncio.get_event_loop()
            task = loop.run_in_executor(None, GetHandler.load_code,
                challenge.uid)
            code = await task
        else:
            code = None

        return ChallengeInterface(challenge, subtasks, code, not viewall)

    def load_code(challenge_uid):
        '''Load the submitted code.

        Args:
            challenge_uid (int): Challenge ID.

        Returns:
            String | None

        '''

        code_root = os.path.join(config.CODE_DIR, '{}'.format(challenge_uid))
        code_main = os.path.join(code_root, 'main.cpp')
        try:
            with open(code_main, 'r') as main_file:
                return main_file.read()
        except:
            return None


class ListHandler(APIHandler):
    '''List challenge handler.'''

    async def process(self, data=None):
        '''Process the request.

        Args:
            data (object): {
                offset (int),
                filter ({
                    user_id (int),
                    problem_uid (int),
                    result (int)
                }) optional
            }

        Returns:
            PartialListInterface | 'Error'

        '''

        offset = int(data['offset'])

        filter_user_uid = None
        filter_problem_uid = None
        filter_result = None
        flt = data.get('filter')
        if flt is not None:
            filter_user_uid = flt.get('user_uid')
            if filter_user_uid is not None:
                filter_user_uid = int(filter_user_uid)

            filter_problem_uid = flt.get('problem_uid')
            if filter_problem_uid is not None:
                filter_problem_uid = int(filter_problem_uid)

            filter_result = flt.get('result')
            if filter_result is not None:
                filter_result = int(filter_result)


        partial_list = await model.challenge.get_list(
            offset=offset,
            user_uid=filter_user_uid,
            problem_uid=filter_problem_uid,
            result=filter_result,
            limit=100)
        if partial_list is None:
            return 'Error'

        count = partial_list['count']
        challenges = partial_list['data']

        ret = []
        for challenge in challenges:
            problem = challenge.problem
            if await view.proset.is_problem_hidden(self.user, problem.uid):
                ret.append(None)
            else:
                ret.append(ChallengeInterface(challenge))

        return PartialListInterface(data=ret, count=count)


class RejudgeHandler(APIHandler):
    '''Rejudge challenge handler.'''

    async def process(self, data=None):
        '''Process the request.

        Args:
            data (object): {
                problem_uid (int) optional
            }

        Returns:
            'Success' | 'Error'

        '''

        problem_uid = None
        if 'problem_uid' in data:
            problem_uid = int(data['problem_uid'])

        if problem_uid is None:
            return 'Error'

        partial_list = await model.challenge.get_list(problem_uid=problem_uid,
            state=JudgeState.done)
        if partial_list is None:
            return 'Error'

        challenges = partial_list['data']
        for challenge in challenges:
            # Reset the challenge.
            await challenge.reset()

            # Get code path.
            code_root = os.path.join(config.CODE_DIR,
                '{}'.format(challenge.uid))
            code_path = os.path.join(code_root, 'main.cpp')

            # Emit the challange worker and wait.
            try:
                await emit_challenge(challenge, code_path)
            except:
                pass

        return 'Success'
