'''User view module'''


import collections
import model.user
import model.scoring
import model.challenge
from model.user import UserLevel, UserCategory
from model.challenge import JudgeState, JudgeResult
from .interface import *
from . import APIHandler, Attribute, Interface


class RegisterHandler(APIHandler):
    '''Register handler.'''

    async def process(self, data):
        '''Process the request.

        Args:
            data (object): {
                'mail' (string),
                'password' (string),
                'name' (string),
            }

        Returns:
            'Success' | 'Eexist'

        '''

        mail = data['mail']
        password = data['password']
        name = data['name']
        if await model.user.create(mail, password, name) is None:
            return 'Eexist'
        else:
            return 'Success'


class LoginHandler(APIHandler):
    '''Login handler.'''

    async def process(self, data):
        '''Process the request.

        Args:
            data (object): { 'mail' (string), 'password' (string) }

        Returns:
            'Success' | 'Error'

        '''

        token = await model.user.gen_token(data['mail'], data['password'])
        if token is None:
            return 'Error'

        self.set_cookie('token', token, httponly=True)
        return 'Success'


class LogoutHandler(APIHandler):
    '''Logout handler.'''

    async def process(self, data):
        '''Process the request.

        Args:
            data (object): {}

        Returns:
            'Success' | 'Error'

        '''

        self.clear_cookie('token')

        return 'Success'


class GetHandler(APIHandler):
    '''Get user information handler.'''

    level = UserLevel.user

    async def process(self, uid=None, data=None):
        '''Process the request.

        Args:
            uid (int, optional): User ID
            data (object): {}

        Returns:
            UserInterface | 'Error'

        '''

        if uid is None:
            uid = self.user.uid
        else:
            uid = int(uid)
            if self.user.uid != uid and self.user.level > UserLevel.kernel:
                return 'Error'

        user = await model.user.get(uid)
        if user is None:
            return 'Error'

        return UserInterface(user)


class ProfileHandler(APIHandler):
    '''Get profile information handler.'''

    async def process(self, uid, data=None):
        '''Process the request.

        Args:
            uid (int): User ID
            data (object): {}

        Returns:
            ProfileInterface | 'Error'

        '''

        uid = int(uid)
        user = await model.user.get(uid)
        if user is None:
            return 'Error'

        rate = await model.scoring.get_user_rate(user)

        return ProfileInterface(user, rate)


class SetHandler(APIHandler):
    '''Set user information handler.'''

    level = UserLevel.user

    async def process(self, uid, data):
        '''Process the request.

        Args:
            uid (int): User ID
            data (object): {
                'name' (string),
                'password' (string, optional),
                'category' (int, optional),
            }

        Returns:
            'Success' | 'Error'

        '''

        uid = int(uid)
        if self.user.uid != uid and self.user.level > UserLevel.kernel:
            return 'Error'

        user = await model.user.get(uid)
        if user is None:
            return 'Error'

        user.name = str(data['name'])

        old_category = user.category
        if self.user.level <= UserLevel.kernel and 'category' in data:
            user.category = UserCategory(data['category'])

        password = data.get('password')
        if password is not None:
            password = str(password)

        if not await user.update(password=password):
            return 'Error'

        await model.scoring.change_category(old_category, user.category)

        return 'Success'


class ListHandler(APIHandler):
    '''List users handler.'''

    level = UserLevel.kernel

    async def process(self, data):
        '''Process the request.

        Args:
            data (object): {}

        Returns:
            [UserInterface] | 'Error'

        '''

        users = await model.user.get_list()
        if users is None:
            return 'Error'

        return [UserInterface(user) for user in users]

class RemoveHandler(APIHandler):
    '''Remove user handler.'''

    level = UserLevel.kernel

    async def process(self, uid, data):
        '''Process the request.

        Args:
            uid (int): User ID
            data (object): {}

        Returns:
            'Success' | 'Error'

        '''

        uid = int(uid)
        user = await model.user.get(uid)
        if user is None:
            return 'Error'

        old_category = user.category

        if not await user.remove():
            return 'Error'

        await model.scoring.change_category(old_category)

        return 'Success'


class StatisticHandler(APIHandler):
    '''Get user statistic handler.'''

    async def process(self, uid, data):
        '''Process the request.

        Args:
            uid (int): User ID
            data (object): {}

        Returns:
            UserStatisticInterface | 'Error'

        '''

        uid = int(uid)
        challenges = await model.challenge.get_list(user_uid=uid)
        if challenges is None:
            return 'Error'

        tried_problems = collections.defaultdict(lambda: {
            'result': JudgeResult.STATUS_ERR
        })
        for challenge in challenges:
            if challenge.state != JudgeState.done:
                continue

            tried_problems[challenge.problem.uid]['result'] = min(
                tried_problems[challenge.problem.uid]['result'],
                challenge.metadata['result'])

        return UserStatisticInterface(tried_problems)
