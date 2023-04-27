from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import User, Message

engine = create_engine('sqlite:///bot_database.db')
Session = sessionmaker(bind=engine)

from contextlib import contextmanager


@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.expunge_all()
        session.close()


def add_message(chat_id, username, content, role='user'):
    with session_scope() as session:
        user = get_or_create_user(chat_id, username)
        message = Message(chat_id=chat_id, content=content, user=user,
                          role=role)
        session.add(message)
        session.flush()


def get_or_create_user(chat_id, username):
    with session_scope() as session:
        user = session.query(User).filter_by(chat_id=chat_id).first()
        if not user:
            user = User(chat_id=chat_id, balance=20, is_admin=False, username=username)
            session.add(user)
            session.flush()
        session.expunge(user)
        return user


def update_balance(username, amount):
    with session_scope() as session:
        user = session.query(User).filter_by(username=username).first()
        if user and (not user.is_admin or amount > 0):
            user.balance += amount


def get_balance(username):
    with session_scope() as session:
        user = session.query(User).filter_by(username=username).first()
        balance = user.balance if user else 0
    return balance


def set_admin(username):
    with session_scope() as session:
        user = session.query(User).filter_by(username=username).first()
        if user:
            user.is_admin = 1


def check_admin(chat_id):
    with session_scope() as session:
        user = session.query(User).filter_by(chat_id=chat_id).first()
        is_admin = user.is_admin if user else 0
    return bool(is_admin)
