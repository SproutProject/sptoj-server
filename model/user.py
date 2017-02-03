'''User model module'''


import bcrypt
import secrets
from . import BaseModel, model_context
from sqlalchemy import Table, Column, Integer, String


class UserModel(BaseModel):

    table = Table('user', BaseModel.metadata,
        Column('uid', Integer, primary_key=True),
        Column('mail', String, index=True, unique=True),
        Column('password', String)
    )


@model_context
async def create(mail, password, conn):
    '''Create a user.
    
    Args:
        mail (string): User mail.
        password (string): User password.

    Returns:
        UserModel | None
    
    '''

    hashpw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hashpw = hashpw.decode('utf-8')

    try:
        user = UserModel(mail=mail, password=hashpw)
        async with conn.begin() as trans:
            await conn.execute(user.save())

        return user
    except:
        return None


"""
async def get(uid):
    '''Get the user.

    Args:
        uid (int): User uid.

    Returns:
        User | None

    '''

    session = ScopedSession()
    try:
        return session.query(User).filter_by(uid=uid).scalar()

    finally:
        session.close()


async def get_token(mail, password):
    '''Check if the mail and password match, then generate a new token.

    Args:
        mail (string): User mail.
        password (string): User password.

    Returns:
        string | None

    '''

    session = ScopedSession()
    rsdb = ScopedRedis()
    try:
        user = session.query(User).filter_by(mail=mail).scalar()
        match = bcrypt.checkpw(password.encode('utf-8'),
            user.password.encode('utf-8'))
        if not match:
            return None
        
        token = None
        while True:
            token = secrets.token_hex(16)
            if rsdb.setnx('TOKEN@{}'.format(token), user.uid):
                break

        return token

    except:
        return None

    finally:
        session.close()


async def acquire(token):
    '''Get user from token.
    
    Args:
        token (string): Token.

    Returns:
        schema.User | None
    
    '''

    rsdb = ScopedRedis()
    uid = rsdb.get('TOKEN@{:032x}'.format(int(token, 16)))
    if uid is None:
        return None

    uid = int(uid)

    session = ScopedSession()
    try:
        return await get(uid)

    except:
        return None

    finally:
        session.close()
"""
