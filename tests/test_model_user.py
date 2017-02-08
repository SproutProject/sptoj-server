'''User model unittest'''


import tests
from model.user import *
from unittest import TestCase


class TestBasic(TestCase):
    '''Create unittest.'''

    @tests.async_test
    async def test_create(self):
        '''Test create.'''

        user = await create('foo', '1234')
        self.assertIsInstance(user, UserModel)
        self.assertEqual(user.uid, 1)

    @tests.async_test
    async def test_exist(self):
        '''Test duplicated user.'''

        self.assertIsInstance(await create('foo', '1234'), UserModel)
        self.assertIsNone(await create('foo', '1234'))

    @tests.async_test
    async def test_list(self):
        '''Test list users.'''

        self.assertIsInstance(await create('foo', '1234'), UserModel)
        self.assertIsNone(await create('foo', '1234'))
        self.assertIsInstance(await create('bar', '12345'), UserModel)
        self.assertIsNone(await create('bar', '12345'))
        users = await get_list()
        self.assertIsNotNone(users)
        self.assertEqual(users[0].mail, 'foo')
        self.assertEqual(users[1].mail, 'bar')

    @tests.async_test
    async def test_update(self):
        '''Test update user.'''

        user = await create('foo', '1234')
        self.assertIsInstance(user, UserModel)
        self.assertEqual(user.level, UserLevel.user)
        user.level = UserLevel.kernel
        self.assertTrue(await user.update(password='5678'))

        self.assertIsNone(await gen_token('foo', '1234'))
        token = await gen_token('foo', '5678')
        self.assertIsNotNone(token)

        user = await acquire(token)
        self.assertIsNotNone(user)
        self.assertEqual(user.level, UserLevel.kernel)


class TestToken(TestCase):
    '''Token unittest.'''

    @tests.async_test
    async def test_get_token(self):
        '''Test get token.'''

        self.assertIsInstance(await create('foo', '1234'), UserModel)
        self.assertIsNotNone(await gen_token('foo', '1234'))
        self.assertIsNone(await gen_token('foo', '12345'))
        self.assertIsNone(await gen_token('bar', '1234'))
        self.assertIsNone(await gen_token('bar', '12345'))

    @tests.async_test
    async def test_acquire(self):
        '''Test get user from token.'''

        self.assertIsInstance(await create('foo', '1234'), UserModel)
        token = await gen_token('foo', '1234')
        self.assertIsNotNone(token)

        user = await acquire(token)
        self.assertIsNotNone(user)
        self.assertEqual(user.mail, 'foo')
        self.assertIsNone(await acquire('deadbeef'))
