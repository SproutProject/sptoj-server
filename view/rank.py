'''Rank view module.'''

import model.scoring
import model.user
import view.proset
from model.user import UserCategory
from .interface import *
from . import APIHandler


class ListHandler(APIHandler):
    '''List handler.'''

    async def process(self, uid, data):
        '''Process the request.

        Args:
            uid (int): Problem set ID.
            data (object): {}

        Returns:
            RankInterface | 'Error'

        '''

        try:
            uid = int(uid)
            proset = await view.proset.get_proset(self.user, uid)
            if proset is None or proset.hidden:
                return 'Error'

            proitems = await proset.list(hidden=False)
            if proitems is None:
                return 'Error'

            users = await model.user.get_list(
                category=UserCategory(proset.metadata['category']))
            if users is None:
                return 'Error'

            for user in users:
                rate = await model.scoring.get_user_score(user,
                    spec_proset_uid=proset.uid)
                print(user.uid, rate)

            return 'Error'
        except:
            return 'Error'
