'''User model module'''


import bcrypt
import secrets
from sqlalchemy import Table, Column, Integer, String
from . import BaseModel, model_context


class UserModel(BaseModel):
    '''User model.'''

    table = Table('user', BaseModel.metadata,
        Column('uid', Integer, primary_key=True),
        Column('mail', String, index=True, unique=True),
        Column('password', String)
    )


@model_context
async def create(mail, password, ctx):
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
        user = UserModel(mail=mail, password=hashpw)
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

    user = await (await UserModel.select()
        .where(UserModel.mail == mail)
        .execute(ctx.conn)).first()
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

    return await (await UserModel.select()
        .where(UserModel.uid == uid)
        .execute(ctx.conn)).first()


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

    return await (await UserModel.select()
        .where(UserModel.uid == uid)
        .execute(ctx.conn)).first()

