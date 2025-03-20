from db_config import engine
from model import Base


def drop_tables():
    Base.metadata.drop_all(engine)


if __name__ == "__main__":
    drop_tables()