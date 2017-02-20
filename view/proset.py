'''Proset view module'''


import config
import model.proset
import model.problem
import model.challenge
import model.scoring
import view.challenge
import os
import asyncio
from datetime import datetime
from model import model_context
from model.user import UserLevel, UserCategory
from model.proset import ProItemModel
from .interface import *
from . import APIHandler, Attribute, Interface


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
    if proitem is None:
        return None

    if proitem.hidden:
        if user is None or user.level > UserLevel.kernel:
            return None

    return proitem


@model_context
async def is_problem_hidden(user, problem_uid, ctx):
    '''Check if the problem is hidden.

    Returns:
        True | False

    '''

    if user is not None and user.level <= UserLevel.kernel:
        return False

    try:
        query = (ProItemModel.select()
            .where((ProItemModel.problem.uid == problem_uid) &
                (ProItemModel.hidden == False) &
                (ProItemModel.parent.hidden == False)))
        return (await query.execute(ctx.conn)).rowcount == 0
    except:
        return True


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

        proset = await model.proset.create(data['name'], True, {
            'category': UserCategory.universe
        })
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
            data (object): {
                'name' (string),
                'hidden' (bool),
                'metadata' ({
                    category (int, optional),
                }),
            }

        Returns:
            'Success' | 'Error'

        '''

        uid = int(uid)
        proset = await get_proset(self.user, uid)

        proset.name = str(data['name'])
        proset.hidden = bool(data['hidden'])

        old_category = UserCategory(proset.metadata['category'])
        update_rate = False

        metadata = data['metadata']
        if 'category' in metadata:
            proset.metadata['category'] = int(metadata['category'])
            update_rate = True

        if not await proset.update():
            return 'Error'

        if update_rate:
            await model.scoring.change_category(old_category,
                UserCategory(proset.metadata['category']))

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
        if proset is None:
            return 'Error'

        if 'category' in proset.metadata:
            old_category = UserCategory(proset.metadata['category'])
        else:
            old_category = None

        if not await proset.remove():
            return 'Error'

        await model.scoring.change_category(old_category, None)

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

        await model.scoring.change_problem(problem.uid)

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


class SetItemHandler(APIHandler):
    '''Set problem item handler.'''

    level = UserLevel.kernel

    async def process(self, proset_uid, proitem_uid, data):
        '''Process the request.

        Args:
            proset_uid (int): Problem set ID.
            proitem_uid (int): Problem item ID.
            data (object): {
                'hidden' (bool),
                'deadline' (string),
                'metadata' (object),
            }

        Returns:
            'Success' | 'Error'

        '''

        proset_uid = int(proset_uid)
        proitem_uid = int(proitem_uid)
        proitem = await get_proitem(self.user, proset_uid, proitem_uid)
        if proitem is None:
            return 'Error'

        proitem.hidden = bool(data['hidden'])

        if data['deadline'] is None:
            deadline = None
        else:
            # To UTC timezone
            deadline = datetime.strptime(data['deadline'], '%Y/%m/%d%z')
            deadline = deadline.astimezone()
        proitem.deadline = deadline

        metadata = data['metadata']
        if 'section' in metadata:
            proitem.metadata['section'] = str(metadata['section'])

        if not await proitem.update():
            return 'Error'

        await model.scoring.change_problem(proitem.problem.uid)

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

        problem_uid = proitem.problem.uid

        if not await proitem.remove():
            return 'Error'

        await model.scoring.change_problem(problem_uid)

        return 'Success'
