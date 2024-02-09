import datetime
import unittest
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlalchemy import Column, Integer, MetaData, Table, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from main import app
from simplecrud.database.database_setup import get_session
from simplecrud.database.model import Base, User

client = TestClient(app=app)

_override_engine: AsyncEngine
_async_session_maker: async_sessionmaker[AsyncSession]


@asynccontextmanager
async def generate_async_engine() -> AsyncGenerator[None, None]:
    global _override_engine
    _override_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)

    async with _override_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    global _async_session_maker
    _async_session_maker = async_sessionmaker(_override_engine, expire_on_commit=False)

    await alter_table_to_support_sqlite("user", _override_engine)

    try:
        yield
    finally:
        await _override_engine.dispose()


async def alter_table_to_support_sqlite(
    table_name: str,
    _override_engine: AsyncEngine,
) -> None:
    metadata = MetaData()
    async with _override_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: metadata.reflect(bind=sync_conn))
    if table_name in metadata.tables:
        async with _override_engine.begin() as conn:
            await conn.run_sync(metadata.tables[table_name].drop)

    # SQLite: if a column is INTEGER (not BigInteger) PRIMARY_KEY - then it is AUTO_INCREMENT
    _ = Table(
        table_name,
        metadata,
        Column("id", Integer, primary_key=True),
        extend_existing=True,
    )
    async with _override_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        async with _async_session_maker() as session:
            yield session
    finally:
        await session.close()


async def save_user(async_session: AsyncSession) -> User:
    user = User(
        id=1,
        external_id="user-1",
        first_name="first",
        last_name="last",
        birthday=datetime.datetime.utcnow(),
    )
    async with async_session.begin():
        async_session.add(user)

    return user


class TestUserCrud(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        app.dependency_overrides[get_session] = override_get_session

    async def test_get_user_by_id(self) -> None:
        async with generate_async_engine():
            async with _async_session_maker() as session:
                user = await save_user(session)

            response = client.get(f"/v1/users/{user.external_id}")

            result_user = response.json()

            self.assertEqual(HTTPStatus.OK, response.status_code)
            self.assertEqual(user.external_id, result_user["id"])
            self.assertEqual(user.first_name, result_user["firstName"])
            self.assertEqual(user.last_name, result_user["lastName"])
            self.assertEqual(
                datetime.datetime.strftime(user.birthday, "%Y-%m-%dT%H:%M:%S.%f"),
                result_user["birthday"],
            )

    async def test_get_user_not_found(self) -> None:
        async with generate_async_engine():
            response = client.get("/v1/users/123")
            self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)
            self.assertEqual(
                "User with id '123' doesn't exist",
                response.json()["detail"],
            )

    async def test_save_user(self) -> None:
        create_user_request = {
            "first_name": "first",
            "last_name": "last",
            "birthday": "2023-10-25T10:45:20.895000",
        }

        async with generate_async_engine():
            response = client.post(
                "/v1/users",
                json=create_user_request,
            )

            self.assertEqual(HTTPStatus.CREATED, response.status_code)
            self.assertIsNotNone(response.json()["id"])

            async with _async_session_maker() as session:
                saved_user = await session.scalar(
                    select(User).where(User.external_id == response.json()["id"])
                )

            if saved_user is None:
                self.assertIsNotNone(saved_user)
            else:
                self.assertEqual("first", saved_user.first_name)
                self.assertEqual("last", saved_user.last_name)
                self.assertEqual(
                    "2023-10-25T10:45:20",
                    saved_user.birthday.strftime("%Y-%m-%dT%H:%M:%S"),
                )

    async def test_update_by_id(self) -> None:
        update_user_request_body = {"firstName": "updated", "lastName": "updated"}
        async with generate_async_engine():
            async with _async_session_maker() as session:
                user = await save_user(session)

            response = client.patch(
                f"/v1/users/{user.external_id}", json=update_user_request_body
            )

            self.assertEqual(HTTPStatus.NO_CONTENT, response.status_code)

            async with _async_session_maker() as session:
                updated_user = await session.scalar(
                    select(User).where(User.external_id == user.external_id)
                )

            if updated_user is None:
                self.assertIsNotNone(updated_user)
            else:
                self.assertEqual(user.id, updated_user.id)
                self.assertNotEqual(user.first_name, updated_user.first_name)
                self.assertNotEqual(user.last_name, updated_user.last_name)

                self.assertEqual("updated", updated_user.first_name)
                self.assertEqual("updated", updated_user.last_name)

    async def test_delete_by_id(self) -> None:
        async with generate_async_engine():
            async with _async_session_maker() as session:
                user = await save_user(session)

            response = client.delete(
                f"/v1/users/{user.external_id}",
            )

            self.assertEqual(HTTPStatus.NO_CONTENT, response.status_code)

            async with _async_session_maker() as session:
                deleted_user = await session.scalar(
                    select(User).where(User.external_id == user.external_id)
                )

            self.assertIsNone(deleted_user)
