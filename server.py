'''Main server program'''


import config
import view.user
import view.problem
import view.proset
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
        (r'/user/list', view.user.ListHandler, param),
        (r'/user/get', view.user.GetHandler, param),
        (r'/user/(\d+)/get', view.user.GetHandler, param),
        (r'/user/(\d+)/set', view.user.SetHandler, param),
        (r'/problem/update', view.problem.UpdateHandler, param),
        (r'/problem/list', view.problem.ListHandler, param),
        (r'/proset/create', view.proset.CreateHandler, param),
        (r'/proset/list', view.proset.ListHandler, param),
        (r'/proset/(\d+)/get', view.proset.GetHandler, param),
        (r'/proset/(\d+)/set', view.proset.SetHandler, param),
        (r'/proset/(\d+)/remove', view.proset.RemoveHandler, param),
        (r'/proset/(\d+)/add', view.proset.AddItemHandler, param),
        (r'/proset/(\d+)/list', view.proset.ListItemHandler, param),
        (r'/proset/(\d+)/(\d+)/get', view.proset.GetItemHandler, param),
        (r'/proset/(\d+)/(\d+)/static/(.*)', view.proset.StaticHandler,
            dict(param, path=config.PROBLEM_DIR)),
        (r'/proset/(\d+)/(\d+)/set', view.proset.SetItemHandler, param),
        (r'/proset/(\d+)/(\d+)/remove', view.proset.RemoveItemHandler, param),
        (r'/proset/(\d+)/(\d+)/submit', view.proset.SubmitHandler, param),
        #(r'/challenge/list', view.challenge.ListHandler, param),
        #(r'/challenge/(\d+)/get', view.challenge.GetHandler, param),
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
