"""Database utilities."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from oh_my_gtm.config import AppSettings

Base = declarative_base()


def create_db_engine(settings: AppSettings):
    """Create a SQLAlchemy engine with sane SQLite defaults for tests."""

    connect_args = {}
    engine_kwargs = {"future": True}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if ":memory:" in settings.database_url:
            engine_kwargs["poolclass"] = StaticPool
    return create_engine(
        settings.database_url,
        connect_args=connect_args,
        **engine_kwargs,
    )


def create_session_factory(settings: AppSettings) -> sessionmaker[Session]:
    engine = create_db_engine(settings)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db(session_factory: sessionmaker[Session]) -> None:
    engine = session_factory.kw["bind"]
    Base.metadata.create_all(bind=engine)


def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
