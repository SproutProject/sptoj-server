'''Proset API unittest'''


import tests
import model.user
from unittest import TestCase


class TestBasic(TestCase):
    '''Basic unittest.'''

    @tests.async_test
    async def test_proset(self):
        '''Test proset operations.'''

        await model.user.create('admin', '1234',
            level=model.user.UserLevel.kernel)
        await model.user.create('foo', '1234')
        response = await tests.request('/user/login', {
            'mail': 'admin',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/proset/create', { 'name': 'square' })
        self.assertNotEqual(response, 'Error')
        response = await tests.request('/proset/create', { 'name': 'circle' })
        self.assertNotEqual(response, 'Error')
        response = await tests.request('/proset/create', { 'name': 'ellipse' })
        self.assertNotEqual(response, 'Error')

        response = await tests.request('/proset/list', {})
        self.assertNotEqual(response, 'Error')
        self.assertEqual(len(response), 3)
        square_uid = response[0]['uid']
        ellipse_uid = response[2]['uid']

        response = await tests.request('/proset/{}/get'.format(square_uid), {})
        self.assertNotEqual(response, 'Error')
        self.assertEqual(response['uid'], square_uid)

        response = await tests.request('/proset/{}/set'.format(square_uid), {
            'name': 'tirangle',
            'hidden': False,
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/proset/{}/remove'.format(ellipse_uid),
            {})
        self.assertEqual(response, 'Success')

        response = await tests.request('/user/login', {
            'mail': 'foo',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/proset/list', {})
        self.assertNotEqual(response, 'Error')
        self.assertEqual(len(response), 1)

    @tests.async_test
    async def test_combo(self):
        '''Test basic combo operations.'''

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
        response = await tests.request('/proset/{}/add'.format(proset_uid), {
             'problem_uid': 2
        })
        self.assertNotEqual(response, 'Error')
        proitem_uid = response

        response = await tests.request('/proset/{}/list'.format(proset_uid), {})
        self.assertNotEqual(response, 'Error')
        self.assertEqual(len(response), 2)

        response = await tests.request(
            '/proset/{}/{}/get'.format(proset_uid, proitem_uid), {})
        self.assertNotEqual(response, 'Error')

        with open('./tests/code/2.cpp', 'r') as test_code:
            response = await tests.request(
                '/proset/{}/{}/submit'.format(proset_uid, proitem_uid), {
                    'code': test_code.read(),
                    'lang': 'c++',
                })
            self.assertNotEqual(response, 'Error')

        # Test permission.
        response = await tests.request('/user/login', {
            'mail': 'foo',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request(
            '/proset/{}/{}/get'.format(proset_uid, proitem_uid), {})
        self.assertEqual(response, 'Error')
