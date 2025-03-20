from db_config import engine
from model import Base


def create_tables():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    create_tables()