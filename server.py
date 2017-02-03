'''Main server program'''


import asyncio
import tornado.web
import tornado.platform.asyncio
from tornado.ioloop import IOLoop


def create_application():
    '''Create the main application.'''

    return tornado.web.Application([
        #(r'/user/register', view.user.RegisterHandler),
        #(r'/user/login', view.user.LoginHandler),
        #(r'/user/get', view.user.GetHandler),
        #(r'/user/get/(\d+)', view.user.GetHandler),
    ])


def start_server():
    '''Start the tornado server.'''

    tornado.platform.asyncio.AsyncIOMainLoop().install()

    app = create_application()
    app.listen(6000)

    loop = asyncio.get_event_loop()
    loop.run_forever()


if __name__ == '__main__':
    start_server()
