import pytest
from httpx import AsyncClient


async def register_user(async_client: AsyncClient, email: str, password: str):
    return await async_client.post(
        "/register", json={"email": email, "password": password}
    )


@pytest.mark.anyio
async def test_register_user_success(async_client: AsyncClient):
    response = await register_user(async_client, "test@example.com", "password")
    assert response.status_code == 201
    assert response.json() == {"message": "User registered successfully"}


@pytest.mark.anyio
async def test_registered_user_already_exists(async_client: AsyncClient):
    await register_user(async_client, "test@example.com", "password")
    response = await register_user(async_client, "test@example.com", "password")
    assert response.status_code == 400
    assert response.json() == {"detail": "A user with this email already exists"}
