'''View base module'''


import model.user
import json
import asyncio
import datetime
import redis
import tornado.web


class Attribute(object):
    '''Dummy interface attribute class.'''


class Interface(object):
    '''Dummy interface class.'''


class ResponseEncoder(json.JSONEncoder):
    '''Response JSON Encoder.'''

    def default(self, obj):
        '''Handle custom types.'''

        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, Interface):
            return dict((key, ResponseEncoder.default(self, getattr(obj, key)))
                for key, value in type(obj).__dict__.items()
                    if isinstance(value, Attribute))
        else:
            return obj


def request_context(resp_json=False):
    '''Request context.'''

    def decorator(func):
        '''Decorator.'''

        async def task_wrapper(self, *args, **kwargs):
            '''Aync task wrapper.'''

            if resp_json:
                self.set_header('content-type', 'application/json')

            async with self.engine.acquire() as conn:
                # Setup model context.
                task = asyncio.Task.current_task()
                task._conn = conn
                task._redis = redis.StrictRedis(connection_pool=self.redis_pool)

                # Get authentication.
                token = self.get_cookie('token')
                if token is None:
                    self.user = None
                else:
                    self.user = await model.user.acquire(token)

                # Check request level
                if self.level is not None:
                    if self.user is None or self.user.level > self.level:
                        if resp_json:
                            self.finish(json.dumps('Error'))
                        else:
                            self.set_status(404)
                        return

                return await func(self, *args, **kwargs)

        async def wrapper(*args, **kwargs):
            '''Wrapper.'''

            loop = asyncio.get_event_loop()
            await loop.create_task(task_wrapper(*args, **kwargs))

        return wrapper

    return decorator


class APIHandler(tornado.web.RequestHandler):
    '''API request handler.'''

    level = None

    def initialize(self, engine, redis_pool):
        '''Initialize.
        
        Args:
            engine (object): Database engine.
            redis_pool (object): Redis connection pool.
        
        '''

        self.engine = engine
        self.redis_pool = redis_pool

    @request_context(resp_json=False)
    async def get(self, *args):
        '''Handle the static requests.

        Args:
            *args ([object]): URL parameters.

        '''

        await self.retrieve(*args)

    @request_context(resp_json=True)
    async def post(self, *args):
        '''Handle the API requests.

        All API requests will be encoded in JSON.
        All responses are also in JSON.

        Args:
            *args ([object]): URL parameters.

        '''

        # Get the request data.
        data = json.loads(self.request.body.decode('utf-8'))
        # Call process method to handle the request.
        response = await self.process(*args, data=data)
        # Write the response.
        self.finish(json.dumps(response, cls=ResponseEncoder))

    async def retrieve(self, *args):
        '''Abstract static retrieve method.

        Args:
            *args ([object]): URL parameters.

        '''

        raise NotImplementedError

    async def process(self, *args, data):
        '''Abstract process method.
        
        Args:
            *args ([object]): URL parameters.
            data (object): API data.

        '''

        raise NotImplementedError
