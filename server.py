'''Main server program'''


import config
import view.user
import view.problem
import view.proset
import view.challenge
import asyncio
import tornado.web
import tornado.options
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
        (r'/user/logout', view.user.LogoutHandler, param),
        (r'/user/list', view.user.ListHandler, param),
        (r'/user/get', view.user.GetHandler, param),
        (r'/user/(\d+)/get', view.user.GetHandler, param),
        (r'/user/(\d+)/set', view.user.SetHandler, param),
        (r'/user/(\d+)/remove', view.user.RemoveHandler, param),
        (r'/user/(\d+)/profile', view.user.ProfileHandler, param),
        (r'/user/(\d+)/statistic', view.user.StatisticHandler, param),
        (r'/problem/(\d+)/update', view.problem.UpdateHandler, param),
        (r'/problem/(\d+)/remove', view.problem.RemoveHandler, param),
        (r'/problem/list', view.problem.ListHandler, param),
        (r'/problem/(\d+)/get', view.problem.GetHandler, param),
        (r'/problem/(\d+)/static/(.*)', view.problem.StaticHandler, param),
        (r'/problem/(\d+)/submit', view.problem.SubmitHandler, param),
        (r'/proset/create', view.proset.CreateHandler, param),
        (r'/proset/list', view.proset.ListHandler, param),
        (r'/proset/(\d+)/get', view.proset.GetHandler, param),
        (r'/proset/(\d+)/set', view.proset.SetHandler, param),
        (r'/proset/(\d+)/remove', view.proset.RemoveHandler, param),
        (r'/proset/(\d+)/add', view.proset.AddItemHandler, param),
        (r'/proset/(\d+)/list', view.proset.ListItemHandler, param),
        (r'/proset/(\d+)/(\d+)/get', view.proset.GetItemHandler, param),
        (r'/proset/(\d+)/(\d+)/set', view.proset.SetItemHandler, param),
        (r'/proset/(\d+)/(\d+)/remove', view.proset.RemoveItemHandler, param),
        (r'/challenge/list', view.challenge.ListHandler, param),
        (r'/challenge/rejudge', view.challenge.RejudgeHandler, param),
        (r'/challenge/(\d+)/get', view.challenge.GetHandler, param),
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
    tornado.options.parse_command_line()
    start_server()
