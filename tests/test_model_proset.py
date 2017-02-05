'''Proset model unittest'''


import tests
import model.problem
from model.proset import *
from unittest import TestCase


class TestBasic(TestCase):
    '''Basic unittest.'''

    @tests.async_test
    async def test_create(self):
        '''Test create.'''

        proset = await create('square')
        self.assertIsInstance(proset, ProSetModel)

        proset = await get(proset.uid)
        self.assertIsInstance(proset, ProSetModel)

    @tests.async_test
    async def test_remove(self):
        '''Test remove.'''

        proset = await create('square')
        self.assertIsInstance(proset, ProSetModel)

        self.assertTrue(await remove(proset))
        self.assertFalse(await remove(proset))
        proset = await get(proset.uid)
        self.assertIsNone(proset)

    @tests.async_test
    async def test_item(self):
        '''Test item operations.'''

        problem = await model.problem.create(1000, 'deadbeef', { 'name': 'A' })
        self.assertIsInstance(problem, model.problem.ProblemModel)

        proset = await create('square')
        self.assertIsInstance(proset, ProSetModel)

        proitem = await proset.add(problem)
        self.assertIsInstance(proitem, ProItemModel)

        proitems = await proset.list()
        self.assertEqual(len(proitems), 1)

        self.assertTrue(await proset.remove(proitem))

        proitems = await proset.list()
        self.assertEqual(len(proitems), 0)
