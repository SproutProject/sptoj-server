'''Problem API unittest'''


import tests
import model.user
from unittest import TestCase


class TestUpdate(TestCase):
    '''Update unittest.'''

    @tests.async_test
    async def test_update(self):
        '''Test update.'''

        await model.user.create('foo', '1234', 'Foo')
        response = await tests.request('/user/login', {
            'mail': 'foo',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')
        
        response = await tests.request('/problem/update', {})
        self.assertEqual(response, 'Error')

        await model.user.create('admin', '1234', 'Admin',
            level=model.user.UserLevel.kernel)
        response = await tests.request('/user/login', {
            'mail': 'admin',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/problem/update', {})
        self.assertEqual(response, 'Success')

    @tests.async_test
    async def test_list(self):
        '''Test list.'''

        await model.user.create('admin', '1234', 'Admin',
            level=model.user.UserLevel.kernel)
        response = await tests.request('/user/login', {
            'mail': 'admin',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')
        response = await tests.request('/problem/update', {})
        self.assertEqual(response, 'Success')

        response = await tests.request('/problem/list', {})
        self.assertGreater(len(response), 0)
