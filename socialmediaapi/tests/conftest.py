import os

os.environ["ENV_STATE"] = "test"

from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient, Response

from socialmediaapi.database import engine, metadata, user_table

if os.path.exists("./test.db"):
    os.remove("./test.db")

from socialmediaapi.database import database
from socialmediaapi.main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    await database.connect()

    # ✅ CRITICAL FIX: use engine.begin()
    with engine.begin() as conn:
        metadata.create_all(bind=conn)

    yield

    # ✅ CLEANUP
    for table in reversed(metadata.sorted_tables):
        await database.execute(f"DELETE FROM {table.name}")

    await database.disconnect()


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=client.base_url) as ac:
        yield ac


@pytest.fixture()
async def registered_user(async_client) -> dict:
    user_data = {
        "email": "testuser@example.com",
        "password": "testpassword",
    }
    await async_client.post("/register", json=user_data)
    query = user_table.select().where(user_table.c.email == user_data["email"])
    result = await database.fetch_one(query)
    user_data["id"] = result["id"]
    return user_data


@pytest.fixture()
async def logged_in_token(async_client, confirmed_user) -> str:
    response = await async_client.post("/token", json=confirmed_user)
    return response.json()["access_token"]


@pytest.fixture()
async def confirmed_user(async_client, registered_user) -> dict:
    # Confirm the user
    query = (
        user_table.update()
        .where(user_table.c.email == registered_user["email"])
        .values(confirmed=True)
    )
    await database.execute(query)
    return registered_user


@pytest.fixture(autouse=True)
async def mock_httpx_client(mocker):
    mocked_client = mocker.patch("socialmediaapi.tasks.httpx.AsyncClient")
    mocked_async_client = Mock()
    response = Response(
        status_code=200,
        content=b"Email sent successfully",
        request=("POST", "//"),
    )
    mocked_async_client.post = AsyncMock(return_value=response)
    mocked_client.return_value.__aenter__.return_value = mocked_async_client
    return mocked_async_client
