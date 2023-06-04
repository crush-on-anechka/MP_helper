from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Cookies(Base):
    __tablename__ = 'cookies'

    remixsid = Column(String, primary_key=True)
    remixnsid = Column(String, primary_key=True)
    hash = Column(String, primary_key=True)


class GroupModel(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)


class StatsModel(Base):
    __tablename__ = 'stats'

    id = Column(Integer, autoincrement=True, primary_key=True)
    date = Column(Date)
    post_name = Column(String)
    group_id = Column(ForeignKey('groups.id', ondelete='CASCADE'), index=True)
    followers = Column(Integer)
    reach_daily = Column(Integer)
    cost = Column(Integer)
    clicks = Column(Integer)
    new_follows = Column(Integer)
    reach_all = Column(Integer)
    reach_followers = Column(Integer)
    likes = Column(Integer)
    shares = Column(Integer)
    comments = Column(Integer)


class ActiveModel(Base):
    __tablename__ = 'active'

    id = Column(Integer, autoincrement=True, primary_key=True)
    date = Column(Date)
    group_id = Column(ForeignKey('groups.id', ondelete='CASCADE'), index=True)
