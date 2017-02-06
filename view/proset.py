'''Proset view module'''


import config
import model.proset
import model.problem
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

        proset = await model.proset.get(proset_uid)
        if proset.hidden and self.user.level > UserLevel.kernel:
            return 'Error'

        proitem = await proset.get(proitem_uid)
        if proitem is None:
            return 'Error'

        return ProItemInterface(proitem)
