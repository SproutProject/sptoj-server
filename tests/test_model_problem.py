'''Problem model unittest'''


import tests
from model.problem import *
from unittest import TestCase


class TestBasic(TestCase):
    '''Basic unittest.'''

    @tests.async_test
    async def test_create(self):
        '''Test create.'''

        problem = await create(1000, 'deadbeef', { 'name': 'foo' })
        self.assertIsInstance(problem, ProblemModel)
        self.assertEqual(problem.uid, 1000)

        problem = await get(1000)
        self.assertIsInstance(problem, ProblemModel)
        self.assertEqual(problem.name, 'foo')
        self.assertEqual(problem.revision, 'deadbeef')

        problem = await create(1000, 'deadbeee', { 'name': 'bar' })
        self.assertIsInstance(problem, ProblemModel)

        problem = await get(1000)
        self.assertIsInstance(problem, ProblemModel)
        self.assertEqual(problem.name, 'bar')
        self.assertEqual(problem.revision, 'deadbeee')

    @tests.async_test
    async def test_remove(self):
        '''Test remove.'''

        problem = await create(1000, 'deadbeef', { 'name': 'foo' })
        self.assertIsInstance(problem, ProblemModel)
        self.assertEqual(problem.uid, 1000)

        self.assertTrue(await remove(1000))
        self.assertFalse(await remove(1000))

        problem = await get(1000)
        self.assertIsNone(problem)
