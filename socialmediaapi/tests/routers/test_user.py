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


@pytest.mark.anyio
async def test_login_user_not_exists(async_client: AsyncClient):
    response = await async_client.post(
        "/token", json={"email": "test@example.net", "password": "password"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication failed: user not found"}


@pytest.mark.anyio
async def test_login_user_success(async_client: AsyncClient, registered_user: dict):
    response = await async_client.post(
        "/token",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
