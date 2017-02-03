'''Unittest base module'''


import config
import model
import asyncio
import tornado.platform.asyncio
import aiopg.sa


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

            async with aiopg.sa.create_engine(config.DB_URL) as engine:
                async with engine.acquire() as conn:
                    asyncio.Task.current_task()._conn = conn
                    await func(*args, **kwargs, conn=conn)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(loop.create_task(async_lambda()))

    return wrapper
