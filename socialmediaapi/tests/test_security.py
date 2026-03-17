import pytest

from socialmediaapi import security


@pytest.mark.anyio
async def test_access_token_expires_in():
    expires_in = security.access_token_expires_in()
    assert isinstance(expires_in, int)
    assert expires_in > 0


@pytest.mark.anyio
async def test_create_access_token():
    email = "test@example.com"
    access_token = security.create_access_token(email)
    decoded_token = security.jwt.decode(
        access_token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
    )
    assert decoded_token["sub"] == email
    assert "exp" in decoded_token


@pytest.mark.anyio
async def test_authenticate_user(registered_user):
    user = await security.authenticate_user(
        registered_user["email"], registered_user["password"]
    )
    assert user is not None
    assert user["email"] == registered_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_nonexistent():
    with pytest.raises(Exception):
        await security.authenticate_user("nonexistent@example.com", "wrongpassword")


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user):
    with pytest.raises(Exception):
        await security.authenticate_user(registered_user["email"], "wrongpassword")


@pytest.mark.anyio
async def test_password_hashing():
    password = "mysecretpassword"
    hashed_password = security.get_password_hash(password)
    assert hashed_password != password
    assert security.verify_password(password, hashed_password)


@pytest.mark.anyio
async def test_get_user(registered_user):
    user = await security.get_user(registered_user["email"])
    assert user is not None
    assert user["email"] == registered_user["email"]


@pytest.mark.anyio
async def test_get_nonexistent_user():
    user = await security.get_user("nonexistent@example.com")
    assert user is None
