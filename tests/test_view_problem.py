'''Problem API unittest'''


import tests
import model.user
from view.problem import *
from unittest import TestCase


class TestUpdate(TestCase):
    '''Update unittest.'''

    @tests.async_test
    async def test_update(self):
        '''Test update.'''

        await model.user.create('foo', '1234')
        response = await tests.request('/user/login', {
            'mail': 'foo',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')
        
        response = await tests.request('/problem/update', {})
        self.assertEqual(response, 'Error')

        await model.user.create('admin', '1234',
            level=model.user.UserLevel.kernel)
        response = await tests.request('/user/login', {
            'mail': 'admin',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/problem/update', {})
        self.assertEqual(response, 'Success')
