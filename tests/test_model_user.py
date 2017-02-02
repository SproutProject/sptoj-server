'''User model unittest'''


import tests
import model.user
from unittest import TestCase


class TestCreate(TestCase):
    '''Create unittest.'''

    @tests.async_test
    async def test_create(self):
        '''Test create.'''

        self.assertNotEqual(await model.user.create('foo', '1234'), None)

    @tests.async_test
    async def test_exist(self):
        '''Test duplicated user.'''

        self.assertNotEqual(await model.user.create('foo', '1234'), None)
        self.assertEqual(await model.user.create('foo', '1234'), None)


class TestToken(TestCase):
    '''Token unittest.'''

    @tests.async_test
    async def test_get_token(self):
        '''Test get token.'''

        self.assertNotEqual(await model.user.create('foo', '1234'), None)
        self.assertNotEqual(await model.user.get_token('foo', '1234'), None)
        self.assertEqual(await model.user.get_token('foo', '12345'), None)
        self.assertEqual(await model.user.get_token('bar', '1234'), None)
        self.assertEqual(await model.user.get_token('bar', '12345'), None)

    @tests.async_test
    async def test_acquire(self):
        '''Test get user from token.'''

        self.assertNotEqual(await model.user.create('foo', '1234'), None)
        token = await model.user.get_token('foo', '1234')
        self.assertNotEqual(token, None)

        user = await model.user.acquire(token)
        self.assertNotEqual(user, None)
        self.assertEqual(user.mail, 'foo')
        self.assertEqual(await model.user.acquire('deadbeef'), None)
