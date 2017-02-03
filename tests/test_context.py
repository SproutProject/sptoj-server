'''Context unittest'''


import config
import asyncio
import context
from context import Context
from unittest import TestCase


class TestContext(TestCase):
    def test_context(self):

        async def foo():
            print(Context.database)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(loop.create_task(foo()))
