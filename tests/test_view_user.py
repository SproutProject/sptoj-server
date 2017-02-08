'''User API unittest'''


import tests
import model.user
from unittest import TestCase


class TestRegister(TestCase):
    '''Register unittest.'''

    @tests.async_test
    async def test_register(self):
        '''Test register.'''

        response = await tests.request('/user/register', {
            'mail': 'text@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')
        response = await tests.request('/user/register', {
            'mail': 'test@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')


    @tests.async_test
    async def test_exist(self):
        '''Test duplicated register.'''

        response = await tests.request('/user/register', {
            'mail': 'test@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')
        response = await tests.request('/user/register', {
            'mail': 'test@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Eexist')


class TestLogin(TestCase):
    '''Login unittest.'''

    @tests.async_test
    async def test_login(self):
        '''Test login.'''

        response = await tests.request('/user/register', {
            'mail': 'foo@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')
        response = await tests.request('/user/register', {
            'mail': 'bar@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/user/login', {
            'mail': 'foo@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')
        response = await tests.request('/user/login', {
            'mail': 'bar@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

    @tests.async_test
    async def test_failed(self):
        '''Test login failed.'''

        response = await tests.request('/user/register', {
            'mail': 'foo@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')
        
        response = await tests.request('/user/login', {
            'mail': 'foo@example.com',
            'password': '12345'
        })
        self.assertEqual(response, 'Error')
        response = await tests.request('/user/login', {
            'mail': 'bar@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Error')


class TestGet(TestCase):
    '''Get unittest.'''

    @tests.async_test
    async def test_get(self):
        '''Test get information.'''

        response = await tests.request('/user/get', {})
        self.assertEqual(response, 'Error')

        response = await tests.request('/user/register', {
            'mail': 'foo@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/user/get', {})
        self.assertEqual(response, 'Error')

        response = await tests.request('/user/login', {
            'mail': 'foo@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/user/get', {})
        self.assertEqual(response, { 'uid': 1 })
        response = await tests.request('/user/1/get', {})
        self.assertEqual(response, { 'uid': 1 })

        response = await tests.request('/user/100/get', {})
        self.assertEqual(response, 'Error')

        response = await tests.request('/user/register', {
            'mail': 'bar@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/user/2/get', {})
        self.assertEqual(response, 'Error')


class TestSet(TestCase):
    '''Set unittest.'''

    @tests.async_test
    async def test_get(self):
        '''Test set information.'''

        response = await tests.request('/user/register', {
            'mail': 'foo@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/user/login', {
            'mail': 'foo@example.com',
            'password': '1234',
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/user/get', {})
        self.assertNotEqual(response, 'Error')
        uid = response['uid']

        response = await tests.request('/user/{}/set'.format(uid), {})
        self.assertEqual(response, 'Success')

        response = await tests.request('/user/{}/set'.format(uid), {
            'password': '5678',
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/user/get', {})
        self.assertEqual(response, 'Error')

        response = await tests.request('/user/login', {
            'mail': 'foo@example.com',
            'password': '1234',
        })
        self.assertEqual(response, 'Error')

        response = await tests.request('/user/login', {
            'mail': 'foo@example.com',
            'password': '5678',
        })
        self.assertEqual(response, 'Success')


class TestList(TestCase):
    '''List unittest.'''

    @tests.async_test
    async def test_list(self):
        '''Test get self information.'''

        response = await tests.request('/user/register', {
            'mail': 'foo@example.com',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        await model.user.create('admin', '1234',
            level=model.user.UserLevel.kernel)
        response = await tests.request('/user/login', {
            'mail': 'admin',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/user/list', {})
        self.assertNotEqual(response, 'Error')
        self.assertEqual(len(response), 2)
