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
from . import APIHandler, Attribute, Interface


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

        return ChallengeInterface(challenge, subtasks)
