'''View unittest'''

import tests
import view
import json
from unittest import TestCase


class Foo(view.Interface):
    '''Foo class.'''

    bar = view.Attribute()

    def __init__(self, model):
        '''Initialize.'''

        self.bar = model['bar']


class Woo(view.Interface):
    '''Foo class.'''

    foos = view.Attribute()

    def __init__(self, model):
        '''Initialize.'''

        self.foos = model


class TestInterface(TestCase):
    '''Interface unittest.'''

    @tests.async_test
    async def test_interface(self):
        '''Test interface.'''

        foo = Foo({'bar': 1234})
        self.assertEqual(foo.bar, 1234)

        woo = Woo([foo])
        self.assertEqual(
            json.loads(json.dumps(woo, cls=view.ResponseEncoder)),
            { 'foos': [{ 'bar': 1234 }] })
