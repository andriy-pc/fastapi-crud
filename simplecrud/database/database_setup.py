import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from simplecrud.database.model import Base
from simplecrud.settings import get_mysql_settings
from simplecrud.util.secret_manager_util import get_string_secret

_engine: AsyncEngine
_async_session_maker: async_sessionmaker[AsyncSession]


@asynccontextmanager
async def generate_async_engine() -> AsyncGenerator[None, None]:
    if get_mysql_settings().url is None:
        get_mysql_settings().url = await get_string_secret("MYSQL_URL")
    connect_string = str(get_mysql_settings().url)
    logging.info("creating async engine")
    global _engine, _async_session_maker
    _engine = create_async_engine(
        connect_string,
        connect_args={"init_command": "SET SESSION time_zone='+00:00'"},
        pool_size=get_mysql_settings().pool_size,
        max_overflow=get_mysql_settings().max_overflow,
        pool_recycle=270,
        echo=False,
        query_cache_size=0,
    )
    _async_session_maker = async_sessionmaker(_engine, expire_on_commit=False)
    try:
        yield
    finally:
        logging.info("disposing async engine")
        await _engine.dispose()


async def make_tables() -> None:
    async with _engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        async with _async_session_maker() as session:
            yield session
    finally:
        await session.close()
