'''User view module'''


import model.user
from . import APIHandler, Attribute, Interface


class UserInterface(Interface):
    '''User view interface.'''

    uid = Attribute()

    def __init__(self, user):
        '''Initialize.

        Args:
            user (schema.User): User object.

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

    async def process(self, uid=None, data=None):
        '''Process the request.

        Args:
            data (object): {}

        Returns:
            UserInterface | 'Error'

        '''

        if self.user is None:
            return 'Error'

        if uid is not None and self.user.uid != int(uid):
            return 'Error'

        if uid is None:
            return UserInterface(self.user)
