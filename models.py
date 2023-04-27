from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    balance = Column(Float, default=0.0)
    is_admin = Column(Integer, default=0)
    messages = relationship('Message', back_populates='user')


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('users.chat_id'), nullable=False)
    content = Column(String)
    role = Column(String)
    user = relationship('User', back_populates='messages')


engine = create_engine('sqlite:///bot_database.db')
Base.metadata.create_all(engine)
