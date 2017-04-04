'''Rank view module.'''

import model.scoring
import model.user
import model.challenge
import view.proset
from model.user import UserLevel, UserCategory
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
            [RankerInterface] | 'Error'

        '''

        uid = int(uid)
        proset = await view.proset.get_proset(self.user, uid)
        if proset is None:
            return 'Error'

        show_hidden = False
        if self.user is not None and self.user.level <= UserLevel.kernel:
            show_hidden = True

        proitems = await proset.list(hidden=show_hidden)
        if proitems is None:
            return 'Error'

        # Distinct problem IDs.
        problem_ids = list(set(proitem.problem.uid for proitem in proitems))

        users = await model.user.get_list(
            category=UserCategory(proset.metadata['category']))
        if users is None:
            return 'Error'

        rankers = {}
        for user in users:
            rate = await model.scoring.get_user_score(user,
                spec_proset_uid=proset.uid)
            rankers[user.uid] = {
                'user': user,
                'rate': rate,
                'results': {},
            }

        result_map = await model.challenge.stat_result(rankers.keys(),
            problem_ids)
        if result_map is None:
            return 'Error'

        for key, result in result_map.items():
            user_uid, problem_uid = key
            rankers[user_uid]['results'][problem_uid] = result

        ranker_list = sorted(rankers.values(), key=lambda x: x['rate'],
            reverse=True)

        return [RankerInterface(ranker) for ranker in ranker_list]
