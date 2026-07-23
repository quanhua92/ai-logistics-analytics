from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import Depends, FastAPI, Request
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_db_lifespan(database_url: str):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = create_async_engine(database_url, pool_pre_ping=True)
        app.state.engine = engine
        app.state.session_factory = async_sessionmaker(
            engine, expire_on_commit=False
        )
        yield
        await engine.dispose()

    return lifespan


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    factory = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]
