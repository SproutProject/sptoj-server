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
    hidden = Attribute()

    def __init__(self, proset):
        '''Initialize.

        Args:
            proset (ProSetModel): Problem set model.

        '''

        self.uid = proset.uid
        self.name = proset.name
        self.hidden = proset.hidden


class ProItemInterface(Interface):
    '''Problem item view interface.'''

    uid = Attribute()
    hidden = Attribute()
    problem = Attribute()

    def __init__(self, proitem):
        '''Initialize.

        Args:
            proitem (ProItemModel): Problem item model.

        '''

        self.uid = proitem.uid
        self.hidden = proitem.hidden
        self.problem = ProblemInterface(proitem.problem)


async def get_proset(user, proset_uid):
    '''Check permission and get the proset item.

    Args:
        user (UserModel): User.
        proset_uid (int): Problem set ID.

    Returns:
        ProSetModel | None

    '''

    proset = await model.proset.get(proset_uid)
    if proset is None:
        return None

    if proset.hidden and (user is None or user.level > UserLevel.kernel):
        return None

    return proset


async def get_proitem(user, proset_uid, proitem_uid):
    '''Check permission and get the problem item.

    Args:
        user (UserModel): User.
        proset_uid (int): Problem set ID.
        proitem_uid (int): Problem item ID.

    Returns:
        ProItemModel | None

    '''

    proset = await get_proset(user, proset_uid)
    if proset is None:
        return None

    proitem = await proset.get(proitem_uid)

    if proitem.hidden and (user is None or user.level > UserLevel.kernel):
        return None

    return proitem


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


class GetHandler(APIHandler):
    '''Get problem set information handler.'''

    async def process(self, uid, data=None):
        '''Process the request.

        Args:
            uid (int): Problem set ID.
            data (object): {}

        Returns:
            ProSetInterface | 'Error'

        '''

        uid = int(uid)
        proset = await get_proset(self.user, uid)
        if proset is None:
            return 'Error'

        return ProSetInterface(proset)


class SetHandler(APIHandler):
    '''Set problem set information handler.'''

    level = UserLevel.kernel

    async def process(self, uid, data=None):
        '''Process the request.

        Args:
            uid (int): Problem set ID.
            data (object): { 'name' (string), 'hidden' (bool) }

        Returns:
            'Success' | 'Error'

        '''

        uid = int(uid)
        proset = await get_proset(self.user, uid)

        proset.name = data['name']
        proset.hidden = data['hidden']

        if not await proset.update():
            return 'Error'

        return 'Success'


class RemoveHandler(APIHandler):
    '''Remove problem set handler.'''

    level = UserLevel.kernel

    async def process(self, uid, data=None):
        '''Process the request.

        Args:
            uid (int): Problem set ID.
            data (object): {}

        Returns:
            'Success' | 'Error'

        '''

        uid = int(uid)
        proset = await get_proset(self.user, uid)
        if not await proset.remove():
            return 'Error'

        return 'Success'


class ListHandler(APIHandler):
    '''List problem set handler.'''

    async def process(self, data):
        '''Process the request.

        Args:
            data (object): {}

        Returns:
            [ProSetInterface] | 'Error'

        '''

        show_hidden = False
        if self.user is not None and self.user.level <= UserLevel.kernel:
            show_hidden = True

        prosets = await model.proset.get_list(hidden=show_hidden)
        if prosets is None:
            return 'Error'

        return [ProSetInterface(proset) for proset in prosets]


class AddItemHandler(APIHandler):
    '''Add problem item handler.'''

    level = UserLevel.kernel

    async def process(self, uid, data):
        '''Process the request.

        Args:
            uid (int): Problem set ID.
            data (object): { 'problem_uid' (int) }

        Returns:
            Int | 'Error'

        '''

        uid = int(uid)
        proset = await get_proset(self.user, uid)
        if proset is None:
            return 'Error'

        problem_uid = int(data['problem_uid'])
        problem = await model.problem.get(problem_uid)
        if problem is None:
            return 'Error'

        proitem = await proset.add(problem, True)
        if proitem is None:
            return 'Error'

        return proitem.uid


class ListItemHandler(APIHandler):
    '''List problem item handler.'''

    async def process(self, uid, data):
        '''Process the request.

        Args:
            uid (int): Problem set ID.
            data (object): {}

        Returns:
            [ProItemInterface] | 'Error'

        '''

        uid = int(uid)
        proset = await get_proset(self.user, uid)
        if proset is None:
            return 'Error'

        show_hidden = False
        if self.user is not None and self.user.level <= UserLevel.kernel:
            show_hidden = True

        proitems = await proset.list(hidden=show_hidden)
        if proitems is None:
            return 'Error'

        return [ProItemInterface(proitem) for proitem in proitems]


class GetItemHandler(APIHandler):
    '''Get problem item handler.'''

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


class StaticHandler(APIHandler):
    '''Serve problem static files.'''

    async def retrieve(self, proset_uid, proitem_uid, rel_path):
        '''Process the request.

        Args:
            proset_uid (int): Problem set ID.
            proitem_uid (int): Problem item ID.
            rel_path (string): Relative path. (Assert it has been normalized.)

        '''

        proitem = await get_proitem(self.user, proset_uid, proitem_uid)
        if proitem is None:
            self.set_status(404)
            return

        problem_uid = proitem.problem.uid
        self.set_header('x-accel-redirect',
            '/internal/static/{}/res/http/{}'.format(problem_uid, rel_path))

        self.set_status(200)


class SetItemHandler(APIHandler):
    '''Set problem item handler.'''

    level = UserLevel.kernel

    async def process(self, proset_uid, proitem_uid, data):
        '''Process the request.

        Args:
            proset_uid (int): Problem set ID.
            proitem_uid (int): Problem item ID.
            data (object): { 'hidden' (bool) }

        Returns:
            'Success' | 'Error'

        '''

        proset_uid = int(proset_uid)
        proitem_uid = int(proitem_uid)
        proitem = await get_proitem(self.user, proset_uid, proitem_uid)
        if proitem is None:
            return 'Error'

        proitem.hidden = data['hidden']

        if not await proitem.update():
            return 'Error'

        return 'Success'


class RemoveItemHandler(APIHandler):
    '''Remove problem item handler.'''

    level = UserLevel.kernel

    async def process(self, proset_uid, proitem_uid, data):
        '''Process the request.

        Args:
            proset_uid (int): Problem set ID.
            proitem_uid (int): Problem item ID.
            data (object): {}

        Returns:
            'Success' | 'Error'

        '''

        proset_uid = int(proset_uid)
        proitem_uid = int(proitem_uid)
        proitem = await get_proitem(self.user, proset_uid, proitem_uid)
        if proitem is None:
            return 'Error'

        if not await proitem.remove():
            return 'Error'

        return 'Success'


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
