from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from tracker.config import get_settings
from tracker.models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None
_schema_ready = False


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        database_path = get_settings().database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            _sqlite_url(database_path),
            echo=False,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def init_db() -> None:
    """Create the SQLite file (and parent dir) and apply the ticker/price schema."""
    global _schema_ready
    engine = get_engine()
    if not _schema_ready:
        Base.metadata.create_all(bind=engine)
        _schema_ready = True


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    init_db()
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
