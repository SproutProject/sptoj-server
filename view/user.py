'''User view module'''


import model.user
from model.user import UserLevel
from . import APIHandler, Attribute, Interface


class UserInterface(Interface):
    '''User view interface.'''

    uid = Attribute()

    def __init__(self, user):
        '''Initialize.

        Args:
            user (UserModel): User model.

        '''

        self.uid = user.uid


class RegisterHandler(APIHandler):
    '''Register handler.'''

    async def process(self, data):
        '''Process the request.

        Args:
            data (object): { 'mail' (string), 'password' (string) }

        Returns:
            'Success' | 'Eexist'

        '''

        if await model.user.create(data['mail'], data['password']) is None:
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


class GetHandler(APIHandler):
    '''Get user information handler.'''

    level = UserLevel.user

    async def process(self, uid=None, data=None):
        '''Process the request.

        Args:
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

        return UserInterface(await model.user.get(uid))


class ListHandler(APIHandler):
    '''List users handler.'''

    level = UserLevel.kernel

    async def process(self, uid=None, data=None):
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
