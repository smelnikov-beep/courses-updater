from datetime import date

from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Date

from bot.db.base import Base
from bot.config_reader import config


class Channel(Base):
    __tablename__ = 'channel'

    channel_id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    link = Column(String(255), default=config.default_link)
    post_id = Column(BigInteger)
    active_until = Column(Date)
