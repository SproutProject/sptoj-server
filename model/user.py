'''User model module'''


import enum
import bcrypt
import secrets
from sqlalchemy import Table, Column, Integer, String, Enum
from . import BaseModel, model_context


@enum.unique
class UserLevel(enum.IntEnum):
    user = 3
    kernel = 0


class UserModel(BaseModel):
    '''User model.'''

    __tablename__ = 'user'

    uid = Column('uid', Integer, primary_key=True)
    mail = Column('mail', String, index=True, unique=True)
    password = Column('password', String)
    level = Column('level', Enum(UserLevel))


@model_context
async def create(mail, password, level=UserLevel.user, ctx=None):
    '''Create a user.
    
    Args:
        mail (string): User mail.
        password (string): User password.

    Returns:
        UserModel | None
    
    '''

    hashpw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
    hashpw = hashpw.decode('utf-8')

    try:
        user = UserModel(mail=mail, password=hashpw, level=level)
        await user.save(ctx.conn)
        return user
    except:
        return None


@model_context
async def modify(uid, password, ctx):

    hashpw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
    hashpw = hashpw.decode('utf-8')

    conn = ctx.conn
    async with conn.begin() as trans:
        pass
        #print(sa.select([UserModel]).select_from(UserModel.join(UserModel)))
        #print(sa.select([UserModel]).where(UserModel.uid == uid).as_scalar())


@model_context
async def gen_token(mail, password, ctx):
    '''Check if the mail and password match, then generate a new token.

    Args:
        mail (string): User mail.
        password (string): User password.

    Returns:
        String | None

    '''

    user = await UserModel.select().where(UserModel.mail == mail).first()
    if user is None:
        return None

    match = bcrypt.checkpw(password.encode('utf-8'),
        user.password.encode('utf-8'))
    if not match:
        return None
    
    token = None
    while True:
        token = secrets.token_hex(16)
        if ctx.redis.setnx('TOKEN@{}'.format(token), user.uid):
            break

    return token


@model_context
async def get(uid, ctx):
    '''Get the user.

    Args:
        uid (int): User uid.

    Returns:
        UserModel | None

    '''

    return await UserModel.select().where(UserModel.uid == uid).first()


@model_context
async def acquire(token, ctx):
    '''Get user from token.
    
    Args:
        token (string): Token.

    Returns:
        UserModel | None
    
    '''

    uid = ctx.redis.get('TOKEN@{:032x}'.format(int(token, 16)))
    if uid is None:
        return None

    uid = int(uid)

    return await UserModel.select().where(UserModel.uid == uid).first()
