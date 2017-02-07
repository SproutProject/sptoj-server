'''Config module

Server configuration.

Attributes:
    DB_URL (str): Connection configuration of PostgreSQL.
    REDIS_URL (str): Connection configuration of Redis.

'''


from os import environ
from dotenv import load_dotenv


# Get the path of dotenv file.
dotenv_path = '.env'
if 'ENV' in environ:
    dotenv_path = environ['ENV']

# Load dotenv.
load_dotenv(dotenv_path)

DB_URL = 'postgresql://{}:{}@{}:{}/{}'.format(
    environ.get('DBUSER'), environ.get('DBPASSWD'), environ.get('DBHOST'),
    environ.get('DBPORT'), environ.get('DBNAME'))

REDIS_URL = 'redis://@{}:{}/0'.format(
    environ.get('REDISHOST'), environ.get('REDISPORT'))

PROBLEM_DIR = environ.get('PROBLEMDIR')
CODE_DIR = environ.get('CODEDIR')
CODE_LIMIT = int(environ.get('CODELIMIT'))
