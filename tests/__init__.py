'''Unittest base module'''


import server
import schema
import model
import json
import asyncio
import aiohttp
import threading
import tornado.web
import tornado.platform.asyncio
from tornado.ioloop import IOLoop


# Install AsyncIO to tornado's IOLoop.
tornado.platform.asyncio.AsyncIOMainLoop().install()

# Configure the testing server.
app = server.create_application()
app.listen(7000)

# Initialize thread local storage for cookiejar.
local_test = threading.local()


def async_test(f):
    '''An async unittest decorator.'''

    def wrapper(*args, **kwargs):
        '''Wrapper.'''

        # Reset the testing redis.
        model.ScopedRedis().flushall()

        # Reset the testing database.
        schema.drop_schema()
        schema.create_schema()

        async def async_lambda():
            '''Async lambda function.'''

            async with aiohttp.ClientSession() as http_session:
                local_test.http_session = http_session
                await f(*args, **kwargs)

            local_test.http_session = None

        loop = asyncio.get_event_loop()
        loop.run_until_complete(loop.create_task(async_lambda()))

        # Reset the scoped session.
        model.ScopedSession.remove()

    return wrapper


async def request(suffix, data):
    '''Emit an API request.
    
    Args:
        data (object): API data.

    Returns:
        object
    
    '''

    api_url = 'http://localhost:7000{}'.format(suffix)
    api_data = json.dumps(data)
    async with local_test.http_session.post(api_url, data=api_data) as response:
        return await response.json()
