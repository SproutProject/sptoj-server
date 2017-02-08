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
    level = Column('level', Enum(UserLevel))
    _mail = Column('mail', String, index=True, unique=True)
    _password = Column('password', String)

    @model_context
    async def update(self, password=None, ctx=None):
        '''Save the changes.

        Returns:
            True | False

        '''

        if password is not None:
            hashpw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
            hashpw = hashpw.decode('utf-8')
            self._password = hashpw

        try:
            await self.save(ctx.conn)
            return True
        except:
            return False


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
        user = UserModel(level=level, mail=mail, password=hashpw)
        await user.save(ctx.conn)
        return user
    except:
        return None


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

    try:
        return await (await UserModel.select()
            .where(UserModel.uid == uid)
            .execute(ctx.conn)).first()
    except:
        return None


@model_context
async def acquire(token, ctx):
    '''Get user from token.
    
    Args:
        token (string): Token.

    Returns:
        UserModel | None
    
    '''

    try:
        uid = ctx.redis.get('TOKEN@{:032x}'.format(int(token, 16)))
    except:
        return None

    if uid is None:
        return None

    uid = int(uid)

    try:
        return await (await UserModel.select()
            .where(UserModel.uid == uid)
            .execute(ctx.conn)).first()
    except:
        return None


@model_context
async def get_list(start_uid=0, limit=None, ctx=None):
    '''List the users.

    Args:
        start_uid (int): Lower bound of the user ID.
        limit (int): The size limit.

    Returns:
        [UserModel] | None

    '''

    query = UserModel.select().where(UserModel.uid >= start_uid)
    if limit is not None:
        query = query.limit(limit)

    try:
        users = []
        async for user in (await query.execute(ctx.conn)):
            users.append(user)

        return users
    except:
        return None
