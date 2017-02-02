'''Model base module

Attributes:
    ScopedSession (Session): ORM scoped session.

'''


import config
import redis
import sqlalchemy as sa
import threading
from sqlalchemy.orm import sessionmaker, scoped_session


# Initialize ORM scoped session.
engine = sa.create_engine(config.DB_URL)
ScopedSession = scoped_session(sessionmaker(bind=engine))

# Initialize thread local storage for model.
local_model = threading.local()


def ScopedRedis():
    '''Get scoped redis connection.'''

    if not hasattr(local_model, 'redis_pool'):
        local_model.redis_pool = redis.ConnectionPool.from_url(config.REDIS_URL)

    return redis.StrictRedis(connection_pool=local_model.redis_pool)
