'''Challenge model unittest'''


import tests
import model.user
import model.problem
from model.challenge import *
from unittest import TestCase


class TestBasic(TestCase):
    '''Basic unittest.'''

    @tests.async_test
    async def test_operation(self):
        '''Test basic operations.'''

        user = await model.user.create('foo', '1234', 'Foo')
        problem = await model.problem.create(1000, 'deadbeef', {
            'name': 'foo',
            'test': [
                { 'data': [1, 2], 'weight': 60 },
                { 'data': [3], 'weight': 40 },
            ]
        })
        challenge = await create(user, problem)
        self.assertIsInstance(challenge, ChallengeModel)
        self.assertEqual(challenge.revision, problem.revision)

        challenge = await get(challenge.uid)
        self.assertIsInstance(challenge, ChallengeModel)

        self.assertTrue(await challenge.remove())
        challenge = await get(challenge.uid)
        self.assertIsNone(challenge)
