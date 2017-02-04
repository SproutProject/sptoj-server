import tests
from model import *
from model.user import *
from unittest import TestCase


class TestCreate(TestCase):
    '''Create unittest.'''

    @tests.async_test
    async def test_create(self):
        '''Test create.'''

        self.assertIsInstance(await create('foo', '1234'), UserModel)

    @tests.async_test
    async def test_exist(self):
        '''Test duplicated user.'''

        self.assertIsInstance(await create('foo', '1234'), UserModel)
        self.assertIsNone(await create('foo', '1234'))


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
