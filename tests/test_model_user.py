'''User model unittest'''


import tests
from model.user import *
from unittest import TestCase


class TestBasic(TestCase):
    '''Basic unittest.'''

    @tests.async_test
    async def test_create(self):
        '''Test create.'''

        user = await create('foo', '1234', 'Foo', category=UserCategory.algo)
        self.assertIsInstance(user, UserModel)
        self.assertEqual(user.uid, 1)
        self.assertEqual(user.name, 'Foo')
        self.assertEqual(user.mail, 'foo')
        self.assertEqual(user.category, UserCategory.algo)
        self.assertEqual(user.level, UserLevel.user)

        user = await create('admin', '12345', 'Admin', level=UserLevel.kernel)
        self.assertIsInstance(user, UserModel)
        self.assertEqual(user.uid, 2)
        self.assertEqual(user.name, 'Admin')
        self.assertEqual(user.mail, 'admin')
        self.assertEqual(user.category, UserCategory.universe)
        self.assertEqual(user.level, UserLevel.kernel)

    @tests.async_test
    async def test_exist(self):
        '''Test duplicated user.'''

        self.assertIsInstance(await create('foo', '1234', 'Foo'), UserModel)
        self.assertIsNone(await create('foo', '1234', 'Foo'))

    @tests.async_test
    async def test_list(self):
        '''Test list users.'''

        for i in range(10):
            self.assertIsInstance(
                await create('foo{}'.format(i), '1234', 'Foo'), UserModel)

        users = await get_list()
        self.assertIsNotNone(users)
        self.assertEqual(len(users), 10)
        for i in range(10):
            self.assertEqual(users[i].mail, 'foo{}'.format(i))

        users = await get_list(start_uid=3, limit=3)
        self.assertIsNotNone(users)
        self.assertEqual(len(users), 3)
        for i in range(3):
            self.assertEqual(users[i].mail, 'foo{}'.format(i + 2))

    @tests.async_test
    async def test_update(self):
        '''Test update user.'''

        user = await create('foo', '1234', 'Foo')
        self.assertIsInstance(user, UserModel)
        user.level = UserLevel.kernel
        user.name = 'Boo'
        self.assertTrue(await user.update(password='5678',
            category=UserCategory.algo))

        self.assertIsNone(await gen_token('foo', '1234'))
        token = await gen_token('foo', '5678')
        self.assertIsNotNone(token)

        user = await acquire(token)
        self.assertIsNotNone(user)
        self.assertEqual(user.level, UserLevel.kernel)
        self.assertEqual(user.name, 'Boo')
        self.assertEqual(user.category, UserCategory.algo)

    @tests.async_test
    async def test_remove(self):
        '''Test remove user.'''

        user = await create('foo', '1234', 'Foo')
        self.assertIsInstance(user, UserModel)
        self.assertTrue(await user.remove())
        self.assertIsNone(await gen_token('foo', '1234'))


class TestToken(TestCase):
    '''Token unittest.'''

    @tests.async_test
    async def test_get_token(self):
        '''Test get token.'''

        self.assertIsInstance(await create('foo', '1234', 'Foo'), UserModel)
        self.assertIsNotNone(await gen_token('foo', '1234'))
        self.assertIsNone(await gen_token('foo', '12345'))
        self.assertIsNone(await gen_token('bar', '1234'))
        self.assertIsNone(await gen_token('bar', '12345'))

    @tests.async_test
    async def test_acquire(self):
        '''Test get user from token.'''

        self.assertIsInstance(await create('foo', '1234', 'Foo'), UserModel)
        token = await gen_token('foo', '1234')
        self.assertIsNotNone(token)

        user = await acquire(token)
        self.assertIsNotNone(user)
        self.assertEqual(user.mail, 'foo')
        self.assertIsNone(await acquire('deadbeef'))
