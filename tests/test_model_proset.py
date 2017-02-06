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

        proset = await create('square', False)
        self.assertIsInstance(proset, ProSetModel)

        proset = await get(proset.uid)
        self.assertIsInstance(proset, ProSetModel)
        self.assertEqual(proset.name, 'square')
        self.assertEqual(proset.hidden, False)

        proset = await create('circle', True)
        self.assertIsInstance(proset, ProSetModel)

        proset = await get(proset.uid)
        self.assertIsInstance(proset, ProSetModel)
        self.assertEqual(proset.name, 'circle')
        self.assertEqual(proset.hidden, True)

    @tests.async_test
    async def test_update(self):
        '''Test update.'''

        proset = await create('circle', True)
        self.assertIsInstance(proset, ProSetModel)

        proset.hidden = False
        self.assertTrue(await proset.update())

        proset = await get(proset.uid)
        self.assertIsInstance(proset, ProSetModel)
        self.assertEqual(proset.name, 'circle')
        self.assertEqual(proset.hidden, False)

    @tests.async_test
    async def test_remove(self):
        '''Test remove.'''

        proset = await create('square', False)
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

        proset = await create('square', False)
        self.assertIsInstance(proset, ProSetModel)

        proitem = await proset.add(problem)
        self.assertIsInstance(proitem, ProItemModel)
        proitems = await proset.list()
        self.assertEqual(len(proitems), 1)

        proitem = await proset.add(problem)
        self.assertIsInstance(proitem, ProItemModel)
        proitems = await proset.list()
        self.assertEqual(len(proitems), 2)

        self.assertTrue(await proset.remove(proitem))
        self.assertFalse(await proset.remove(proitem))

        proitems = await proset.list()
        self.assertEqual(len(proitems), 1)
