'''Main server program'''


import config
import view.user
import view.problem
import view.proset
import view.challenge
import asyncio
import tornado.web
import tornado.platform.asyncio
import redis
import aiopg.sa
from tornado.ioloop import IOLoop


def create_application(engine, redis_pool):
    '''Create the main application.'''

    param = {
        'engine': engine,
        'redis_pool': redis_pool
    }
    return tornado.web.Application([
        (r'/user/register', view.user.RegisterHandler, param),
        (r'/user/login', view.user.LoginHandler, param),
        (r'/user/get', view.user.GetHandler, param),
        (r'/user/(\d+)/get', view.user.GetHandler, param),
        (r'/problem/update', view.problem.UpdateHandler, param),
        (r'/problem/list', view.problem.ListHandler, param),
        (r'/proset/create', view.proset.CreateHandler, param),
        (r'/proset/(\d+)/add', view.proset.AddItemHandler, param),
        (r'/proset/(\d+)/(\d+)/get', view.proset.GetItemHandler, param),
    ])


def start_server():
    '''Start the tornado server.'''

    tornado.platform.asyncio.AsyncIOMainLoop().install()

    async def async_lambda():
        '''Async lambda function.'''

        engine = await aiopg.sa.create_engine(config.DB_URL)
        redis_pool = redis.ConnectionPool.from_url(config.REDIS_URL)
        app = create_application(engine, redis_pool)
        app.listen(6000)

    loop = asyncio.get_event_loop()
    loop.create_task(async_lambda())
    loop.run_forever()


if __name__ == '__main__':
    start_server()
