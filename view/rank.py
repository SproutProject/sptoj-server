'''Rank view module.'''


from .interface import *
from . import APIHandler


class ListHandler(APIHandler):
    '''List handler.'''

    async def process(self, data):
        '''Process the request.

        Args:
            data (object): {}

        Returns:
            PartialListInterface | 'Error'

        '''

        pass
