'''Proset API unittest'''


import tests
import model.user
from unittest import TestCase


class TestBasic(TestCase):
    '''Basic unittest.'''

    @tests.async_test
    async def test_create(self):
        '''Test create.'''

        await model.user.create('admin', '1234',
            level=model.user.UserLevel.kernel)
        await model.user.create('foo', '1234')
        response = await tests.request('/user/login', {
            'mail': 'admin',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/problem/update', {})
        self.assertEqual(response, 'Success')

        response = await tests.request('/proset/create', { 'name': 'square' })
        self.assertNotEqual(response, 'Error')
        proset_uid = response

        response = await tests.request('/proset/{}/add'.format(proset_uid), {
             'problem_uid': 2
        })
        self.assertNotEqual(response, 'Error')
        proitem_uid = response

        response = await tests.request(
            '/proset/{}/{}/get'.format(proset_uid, proitem_uid), {})
        self.assertNotEqual(response, 'Error')

        response = await tests.request('/user/login', {
            'mail': 'foo',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request(
            '/proset/{}/{}/get'.format(proset_uid, proitem_uid), {})
        self.assertEqual(response, 'Error')
