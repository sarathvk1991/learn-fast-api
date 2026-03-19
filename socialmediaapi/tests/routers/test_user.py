import pytest
from fastapi import BackgroundTasks
from httpx import AsyncClient


async def register_user(async_client: AsyncClient, email: str, password: str):
    return await async_client.post(
        "/register", json={"email": email, "password": password}
    )


@pytest.mark.anyio
async def test_register_user_success(async_client: AsyncClient):
    response = await register_user(async_client, "test@example.com", "password")
    assert response.status_code == 201
    assert "User registered successfully" in response.json()["message"]


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
async def test_login_user_success(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post(
        "/token",
        json={
            "email": confirmed_user["email"],
            "password": confirmed_user["password"],
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.anyio
async def test_confirm_user_success(async_client: AsyncClient, mocker):
    spy = mocker.spy(BackgroundTasks, "add_task")
    # First, register the user to get the confirmation token
    await register_user(async_client, "test@example.com", "password")
    confirmation_url = str(spy.call_args[1]["confirmation_link"])
    response = await async_client.get(confirmation_url)
    assert response.status_code == 200
    assert response.json() == {"detail": "User confirmed successfully"}


@pytest.mark.anyio
async def test_confirm_user_invalid_token(async_client: AsyncClient):
    response = await async_client.get("/confirm/invalidtoken")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_confirm_user_expired_token(async_client: AsyncClient, mocker):
    mocker.patch(
        "socialmediaapi.security.confirm_token_expires_in", return_value=-1
    )  # Set token to expire immediately
    spy = mocker.spy(BackgroundTasks, "add_task")
    # First, register the user to get the confirmation token
    await register_user(async_client, "test@example.com", "password")
    confirmation_url = str(spy.call_args[1]["confirmation_link"])

    response = await async_client.get(confirmation_url)
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_user_not_confirmed(
    async_client: AsyncClient, registered_user: dict
):
    response = await async_client.post(
        "/token",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication failed: email not confirmed"}
