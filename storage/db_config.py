from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine("mysql://andrew:Kasavior47%40@db/storage")


def make_session():
    return sessionmaker(bind=engine)()