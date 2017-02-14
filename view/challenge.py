'''Proset view module'''


import config
import model.challenge
import os
import json
import enum
import asyncio
import aiohttp
from datetime import datetime
from model.user import UserLevel
from model.challenge import JudgeState
from view.user import UserInterface
from view.problem import ProblemInterface
from . import APIHandler, Attribute, Interface


class ChallengeInterface(Interface):
    '''Challenge view interface.'''

    uid = Attribute()
    state = Attribute()
    timestamp = Attribute()
    metadata = Attribute()
    submitter = Attribute()
    problem = Attribute()
    subtasks = Attribute()

    def __init__(self, challenge, subtasks):
        '''Initialize.

        Args:
            challenge (ChallengeModel): Challenge model.

        '''

        self.uid = challenge.uid
        self.state = int(challenge.state)
        self.timestamp = challenge.timestamp
        self.metadata = challenge.metadata
        self.submitter = UserInterface(challenge.submitter)
        self.problem = ProblemInterface(challenge.problem)
        self.subtasks = [SubtaskInterface(subtask) for subtask in subtasks]


class SubtaskInterface(Interface):
    '''Subtask view interface.'''

    uid = Attribute()
    index = Attribute()
    state = Attribute()
    metadata = Attribute()

    def __init__(self, subtask):
        '''Initialize.

        Args:
            subtask (SubtaskModel): Subtask model.

        '''

        self.uid = subtask.uid
        self.index = subtask.index
        self.state = int(subtask.state)
        self.metadata = subtask.metadata


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

        if self.user is None or self.user.level > UserLevel.kernel:
            if await challenge.is_hidden():
                return 'Error'

        subtasks = await challenge.list()
        if subtasks is None:
            return 'Error'

        return ChallengeInterface(challenge, subtasks)
