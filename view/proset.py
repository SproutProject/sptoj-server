'''Proset view module'''


import config
import model.proset
import model.problem
import model.challenge
import os
import asyncio
from model.user import UserLevel
from view.problem import ProblemInterface
from . import APIHandler, Attribute, Interface


class ProSetInterface(Interface):
    '''Problem set view interface.'''

    uid = Attribute()
    name = Attribute()

    def __init__(self, proset):
        '''Initialize.

        Args:
            proset (ProSetModel): Problem set model.

        '''

        self.uid = proset.uid
        self.name = proset.name


class ProItemInterface(Interface):
    '''Problem item view interface.'''

    uid = Attribute()
    problem = Attribute()

    def __init__(self, proitem):
        '''Initialize.

        Args:
            proitem (ProItemModel): Problem item model.

        '''

        self.uid = proitem.uid
        self.problem = ProblemInterface(proitem.problem)


async def get_proitem(user, proset_uid, proitem_uid):
    '''Check permission and get the problem item.

    Args:
        user (UserModel): User.
        proset_uid (int): Problem set ID.
        proitem_uid (int): Problem item ID.

    Returns:
        ProItemModel | None

    '''

    proset = await model.proset.get(proset_uid)
    if proset.hidden:
        if user is None:
            return None
        if user.level > UserLevel.kernel:
            return None

    return await proset.get(proitem_uid)


class CreateHandler(APIHandler):
    '''Create proset handler.'''

    level = UserLevel.kernel

    async def process(self, data):
        '''Process the request.

        Args:
            data (object): { 'name' (string) }

        Returns:
            Int | 'Error'

        '''

        proset = await model.proset.create(data['name'], True)
        if proset is None:
            return 'Error'

        return proset.uid


class AddItemHandler(APIHandler):
    '''Add proitem handler.'''

    level = UserLevel.kernel

    async def process(self, proset_uid, data):
        '''Process the request.

        Args:
            data (object): { 'problem_uid' (int) }

        Returns:
            Int | 'Error'

        '''

        proset = await model.proset.get(proset_uid)
        if proset is None:
            return 'Error'

        problem_uid = int(data['problem_uid'])
        problem = await model.problem.get(problem_uid)
        if problem is None:
            return 'Error'

        proitem = await proset.add(problem)
        if proitem is None:
            return 'Error'

        return proitem.uid


class GetItemHandler(APIHandler):
    '''Get proitem handler.'''

    async def process(self, proset_uid, proitem_uid, data):
        '''Process the request.

        Args:
            proset_uid (int): Problem set ID.
            proitem_uid (int): Problem item ID.
            data (object): {}

        Returns:
            ProItemInterface | 'Error'

        '''

        proset_uid = int(proset_uid)
        proitem_uid = int(proitem_uid)
        proitem = await get_proitem(self.user, proset_uid, proitem_uid)
        if proitem is None:
            return 'Error'

        return ProItemInterface(proitem)


class SubmitHandler(APIHandler):
    '''Submit handler.'''

    level = UserLevel.user

    async def process(self, proset_uid, proitem_uid, data):
        '''Process the request.

        Args:
            proset_uid (int): Problem set ID.
            proitem_uid (int): Problem item ID.
            data (object): { 'code' (string), 'lang' (string) }

        Returns:
            Int | 'Error'

        '''

        proset_uid = int(proset_uid)
        proitem_uid = int(proitem_uid)
        code = data['code']
        lang = data['lang']

        if len(code) > config.CODE_LIMIT:
            return 'Error'

        proitem = await get_proitem(self.user, proset_uid, proitem_uid)
        if proitem is None:
            return 'Error'

        challenge = await model.challenge.create(self.user, proitem.problem)
        if challenge is None:
            return 'Error'

        loop = asyncio.get_event_loop()

        task = loop.run_in_executor(None, SubmitHandler.store_code,
            challenge.uid, code)
        code_path = await task
        if code_path is None:
            await challenge.remove()
            return 'Error'

        # Queue the challange.
        loop.create_task(SubmitHandler.emit_challenge(challenge, code_path))

        return challenge.uid

    def store_code(challenge_uid, code):
        '''Store the submitted code.

        Args:
            challenge_uid (int): Challenge ID.
            code (string): Code.

        Returns:
            String | None

        '''

        code_root = os.path.join(config.CODE_DIR, '{}'.format(challenge_uid))
        code_main = os.path.join(code_root, 'main')
        try:
            os.mkdir(code_root, mode=0o755)
            with open(code_main, 'w') as main_file:
                main_file.write(code)
            return code_main
        except:
            return None

    async def emit_challenge(challenge, code_path):
        '''Emit the challenge and update the results.

        Args:
            challenge (ChallengeModel): Challenge.
            code_path (string): File path of the code.
            
        '''
