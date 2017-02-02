'''Database schema module'''


import config
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    '''User class.

    Attributes:
        uid (int): Unique ID.
        mail (string): Mail.

    '''

    __tablename__ = 'user'

    uid = Column(Integer, primary_key=True)
    mail = Column(String, index=True, unique=True)
    password = Column(String)


def create_schema():
    '''Create database schema.'''

    engine = sa.create_engine(config.DB_URL)
    Base.metadata.create_all(engine)
    engine.dispose()


def drop_schema():
    '''Drop database schema.'''

    engine = sa.create_engine(config.DB_URL)
    Base.metadata.drop_all(engine)
    engine.dispose()


if __name__ == '__main__':
    create_schema()
