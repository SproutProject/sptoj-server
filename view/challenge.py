'''Proset view module'''


import config
import model.challenge
import os
import asyncio
from datetime import datetime
from model.user import UserLevel
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
