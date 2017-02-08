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

        proset.name = 'square'
        proset.hidden = False
        self.assertTrue(await proset.update())

        proset = await get(proset.uid)
        self.assertIsInstance(proset, ProSetModel)
        self.assertEqual(proset.name, 'square')
        self.assertEqual(proset.hidden, False)

    @tests.async_test
    async def test_remove(self):
        '''Test remove.'''

        proset = await create('square', False)
        self.assertIsInstance(proset, ProSetModel)

        self.assertTrue(await proset.remove())
        proset = await get(proset.uid)
        self.assertIsNone(proset)

    @tests.async_test
    async def test_get_list(self):
        '''Test get_list.'''

        proset = await create('square', False)
        self.assertIsInstance(proset, ProSetModel)
        proset = await create('circle', False)
        self.assertIsInstance(proset, ProSetModel)
        proset = await create('tirangle', True)
        self.assertIsInstance(proset, ProSetModel)

        prosets = await get_list()
        self.assertIsNotNone(prosets)
        self.assertEqual(len(prosets), 2)

        prosets = await get_list(hidden=True)
        self.assertIsNotNone(prosets)
        self.assertEqual(len(prosets), 3)

    @tests.async_test
    async def test_item(self):
        '''Test item operations.'''

        problem = await model.problem.create(1000, 'deadbeef', { 'name': 'A' })
        self.assertIsInstance(problem, model.problem.ProblemModel)

        proset = await create('square', False)
        self.assertIsInstance(proset, ProSetModel)

        proitem = await proset.add(problem, False)
        self.assertIsInstance(proitem, ProItemModel)

        proitem = await proset.add(problem, False)
        self.assertIsInstance(proitem, ProItemModel)

        problem = await model.problem.create(1001, 'deadbeef', { 'name': 'B' })
        self.assertIsInstance(problem, model.problem.ProblemModel)

        proitem = await proset.add(problem, True)
        self.assertIsInstance(proitem, ProItemModel)

        proitems = await proset.list()
        self.assertEqual(len(proitems), 2)
        proitems = await proset.list(hidden=True)
        self.assertEqual(len(proitems), 3)

        self.assertEqual(proitems[2].problem.uid, 1001)

        self.assertTrue(await proitems[0].remove())

        proitems = await proset.list()
        self.assertEqual(len(proitems), 1)
