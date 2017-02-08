'''Proset API unittest'''


import tests
import model.user
from unittest import TestCase


class TestBasic(TestCase):
    '''Basic unittest.'''

    async def init_users(self):
        '''Initialize user environment.'''

        await model.user.create('admin', '1234',
            level=model.user.UserLevel.kernel)
        await model.user.create('foo', '1234')
        response = await tests.request('/user/login', {
            'mail': 'admin',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

    async def login_admin(self):
        '''Login admin user.'''

        response = await tests.request('/user/login', {
            'mail': 'admin',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

    async def login_user(self):
        '''Login normal user.'''

        response = await tests.request('/user/login', {
            'mail': 'foo',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

    @tests.async_test
    async def test_proset(self):
        '''Test proset operations.'''

        await self.init_users()

        await self.login_admin()

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

        await self.login_user()

        response = await tests.request('/proset/list', {})
        self.assertNotEqual(response, 'Error')
        self.assertEqual(len(response), 1)

    @tests.async_test
    async def test_combo(self):
        '''Test basic combo operations.'''

        await self.init_users()

        await self.login_admin()

        response = await tests.request('/problem/update', {})
        self.assertEqual(response, 'Success')

        response = await tests.request('/proset/create', { 'name': 'square' })
        self.assertNotEqual(response, 'Error')
        proset_uid = response

        response = await tests.request('/proset/{}/add'.format(proset_uid), {
             'problem_uid': 2
        })
        self.assertNotEqual(response, 'Error')
        dummy_proitem_uid = response

        response = await tests.request('/proset/{}/add'.format(proset_uid), {
             'problem_uid': 2
        })
        self.assertNotEqual(response, 'Error')
        hidden_proitem_uid = response

        response = await tests.request('/proset/{}/add'.format(proset_uid), {
             'problem_uid': 2
        })
        self.assertNotEqual(response, 'Error')
        proitem_uid = response

        response = await tests.request(
            '/proset/{}/{}/remove'.format(proset_uid, dummy_proitem_uid), {})
        self.assertEqual(response, 'Success')

        response = await tests.request(
            '/proset/{}/{}/set'.format(proset_uid, proitem_uid), {
                'hidden': False,   
            })
        self.assertEqual(response, 'Success')

        response = await tests.request('/proset/{}/list'.format(proset_uid), {})
        self.assertNotEqual(response, 'Error')
        self.assertEqual(len(response), 2)

        await self.login_user()

        response = await tests.request(
            '/proset/{}/{}/get'.format(proset_uid, proitem_uid), {})
        self.assertEqual(response, 'Error')

        await self.login_admin()

        response = await tests.request('/proset/{}/set'.format(proset_uid), {
            'name': 'square',
            'hidden': False,
        })
        self.assertEqual(response, 'Success')

        await self.login_user()

        response = await tests.request(
            '/proset/{}/{}/get'.format(proset_uid, hidden_proitem_uid), {})
        self.assertEqual(response, 'Error')

        response = await tests.request('/proset/{}/list'.format(proset_uid), {})
        self.assertNotEqual(response, 'Error')
        self.assertEqual(len(response), 1)

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
