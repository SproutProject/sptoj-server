'''Basic simulation unittest'''


import tests
import model.user
from unittest import TestCase


class TestSubmit(TestCase):

    @tests.async_test
    async def test_submit(self):

        await model.user.create('admin', '1234',
            level=model.user.UserLevel.kernel)
        response = await tests.request('/user/login', {
            'mail': 'admin',
            'password': '1234'
        })
        self.assertEqual(response, 'Success')

        response = await tests.request('/problem/update', {})
        self.assertEqual(response, 'Success')

        
