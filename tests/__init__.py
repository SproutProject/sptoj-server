'''Unittest base module'''


import config
import model
import asyncio
import tornado.platform.asyncio
import aiopg.sa
import redis


# Install AsyncIO to tornado's IOLoop.
tornado.platform.asyncio.AsyncIOMainLoop().install()


def async_test(func):
    '''An async unittest decorator.'''

    def wrapper(*args, **kwargs):
        '''Wrapper.'''

        model.drop_schemas(config.DB_URL)
        model.create_schemas(config.DB_URL)

        async def async_lambda():
            '''Async lambda function.'''

            rsconn = redis.StrictRedis.from_url(config.REDIS_URL)

            async with aiopg.sa.create_engine(config.DB_URL) as engine:
                async with engine.acquire() as conn:
                    task = asyncio.Task.current_task()
                    task._conn = conn
                    task._redis = rsconn
                    await func(*args, **kwargs)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(loop.create_task(async_lambda()))

    return wrapper
