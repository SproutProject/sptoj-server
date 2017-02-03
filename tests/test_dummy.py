import tests
from model.user import *
from unittest import TestCase


class TestDummy(TestCase):

    @tests.async_test
    async def test_dummy(self, conn):
        user = await create('test', '1234')
        self.assertIsInstance(user, UserModel)
        user = await create('test', '1234')
        self.assertIsNone(user)
