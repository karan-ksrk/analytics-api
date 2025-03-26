import sqlmodel
from sqlmodel import SQLModel, Session
import timescaledb
from .config import DATABASE_URL, DB_TIMEZONE
from utils import bcolors


if DATABASE_URL == "":
    raise NotImplementedError("DATABASE_URL is not set")


engine = timescaledb.create_engine(DATABASE_URL, timezone=DB_TIMEZONE)


def init_db():
    print(bcolors.OKGREEN, "creating database")
    SQLModel.metadata.create_all(engine)
    print(bcolors.OKGREEN, "creating hypertables", )
    timescaledb.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
