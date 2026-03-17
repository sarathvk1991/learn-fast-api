import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from socialmediaapi.database import metadata, user_table

os.environ["ENV_STATE"] = "test"

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
    yield
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
async def logged_in_token(async_client, registered_user) -> str:
    response = await async_client.post("/token", json=registered_user)
    return response.json()["access_token"]
