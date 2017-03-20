'''Unittest base module'''


import config
import server
import model
import json
import asyncio
import tornado.platform.asyncio
import aiopg.sa
import redis
import aiohttp
import shutil
import os


# Install AsyncIO to tornado's IOLoop.
tornado.platform.asyncio.AsyncIOMainLoop().install()

loop = asyncio.get_event_loop()
engine = loop.run_until_complete(aiopg.sa.create_engine(config.DB_URL))
redis_pool = redis.ConnectionPool.from_url(config.REDIS_URL)
app = server.create_application(engine, redis_pool)
app.listen(7000)


def async_test(func):
    '''An async unittest decorator.'''

    def wrapper(*args, **kwargs):
        '''Wrapper.'''

        try:
            shutil.rmtree('./tests/tmp')
        except FileNotFoundError:
            pass
        os.mkdir('./tests/tmp', mode=0o755)
        os.mkdir('./tests/tmp/code', mode=0o755)

        model.drop_schemas(config.DB_URL)
        model.create_schemas(config.DB_URL)

        async def async_lambda():
            '''Async lambda function.'''

            global http_session

            rsconn = redis.StrictRedis.from_url(config.REDIS_URL)

            async with aiopg.sa.create_engine(config.DB_URL) as engine:
                async with engine.acquire() as conn:
                    task = asyncio.Task.current_task()
                    task._conn = conn
                    task._redis = rsconn

                    async with aiohttp.ClientSession() as http_client:
                        http_session = http_client
                        await func(*args, **kwargs)

                    http_session = None

        loop = asyncio.get_event_loop()
        loop.run_until_complete(loop.create_task(async_lambda()))

        shutil.rmtree('./tests/tmp')

    return wrapper


async def request(suffix, data):
    '''Emit an API request.

    Args:
        data (object): API data.

    Returns:
        object

    '''

    global http_session

    api_url = 'http://localhost:7000{}'.format(suffix)
    api_data = json.dumps(data)
    async with http_session.post(api_url, data=api_data) as response:
        return await response.json()
