'''View unittest'''

import tests
import view
import json
from datetime import datetime
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

        date = datetime.strptime('1970/01/01+0800', '%Y/%m/%d%z')
        foo = Foo({'bar': date})
        goo = Foo({'bar': 10})
        self.assertEqual(foo.bar, date)
        self.assertEqual(goo.bar, 10)

        woo = Woo([foo, goo])
        self.assertEqual(
            json.loads(json.dumps(woo, cls=view.ResponseEncoder)),
            { 'foos': [
                { 'bar': date.isoformat() },
                { 'bar': 10 }
            ] })
