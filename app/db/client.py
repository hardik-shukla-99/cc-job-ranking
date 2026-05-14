from typing import Any, Generator

from fastapi import FastAPI
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from starlette.requests import Request

from app.core import settings


class Base(DeclarativeBase):
    pass


class DBClient:
    _engine: Engine
    _session_factory: Any = None

    @classmethod
    def initialise(cls, app: FastAPI) -> None:
        cls._engine = create_engine(
            settings.db_url,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            echo=settings.DB_ECHO,
        )
        cls._session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls._engine,
            expire_on_commit=False,
        )
        app.state.db_engine = cls._engine
        app.state.db_session_factory = cls._session_factory
        cls._create_tables()

    @classmethod
    def _create_tables(cls) -> None:
        Base.metadata.create_all(bind=cls._engine)

    @staticmethod
    def get_db_session(request: Request) -> Generator[Session, None, None]:
        session: Session = request.app.state.db_session_factory()
        try:
            yield session
        finally:
            session.commit()
            session.close()
