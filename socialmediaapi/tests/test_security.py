import pytest

from socialmediaapi import security


@pytest.mark.anyio
async def test_access_token_expires_in():
    expires_in = security.access_token_expires_in()
    assert isinstance(expires_in, int)
    assert expires_in > 0


@pytest.mark.anyio
async def test_confirm_token_expires_in():
    expires_in = security.confirm_token_expires_in()
    assert isinstance(expires_in, int)
    assert expires_in > 0


@pytest.mark.anyio
async def test_create_confirmation_token():
    email = "test@example.com"
    confirmation_token = security.create_confirmation_token(email)
    decoded_token = security.jwt.decode(
        confirmation_token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
    )
    assert decoded_token["sub"] == email
    assert "exp" in decoded_token
    assert decoded_token["type"] == "confirmation"


@pytest.mark.anyio
async def test_valide_token_type():
    email = "test@example.com"
    access_token = security.create_access_token(email)
    confirmation_token = security.create_confirmation_token(email)
    decoded_access_token = security.jwt.decode(
        access_token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
    )
    decoded_confirmation_token = security.jwt.decode(
        confirmation_token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
    )
    assert decoded_access_token["type"] == "access"
    assert decoded_confirmation_token["type"] == "confirmation"
    assert decoded_access_token["sub"] == email
    assert decoded_confirmation_token["sub"] == email


@pytest.mark.anyio
async def test_create_access_token():
    email = "test@example.com"
    access_token = security.create_access_token(email)
    decoded_token = security.jwt.decode(
        access_token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
    )
    assert decoded_token["sub"] == email
    assert "exp" in decoded_token
    assert decoded_token["type"] == "access"


@pytest.mark.anyio
async def test_authenticate_user(confirmed_user):
    user = await security.authenticate_user(
        confirmed_user["email"], confirmed_user["password"]
    )
    assert user is not None
    assert user["email"] == confirmed_user["email"]


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


@pytest.mark.anyio
async def test_get_current_user(registered_user):
    access_token = security.create_access_token(registered_user["email"])
    current_user = await security.get_current_user(access_token)
    assert current_user is not None
    assert current_user["email"] == registered_user["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token(registered_user):
    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalid_token")


@pytest.mark.anyio
async def test_get_current_user_wrong_token_type(registered_user):
    confirmation_token = security.create_confirmation_token(registered_user["email"])
    with pytest.raises(security.HTTPException):
        await security.get_current_user(confirmation_token)


@pytest.mark.anyio
async def test_get_subject_for_expired_token(registered_user):
    # Create a token that expires immediately
    expired_token = security.jwt.encode(
        {"sub": registered_user["email"], "type": "access", "exp": 0},
        security.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token(expired_token, "access")
    assert "Token has expired" in str(exc_info.value.detail)


@pytest.mark.anyio
async def test_get_subject_for_invalid_token(registered_user):
    # Create a token that expires immediately
    invalid_token = "invalid.token.value"
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token(invalid_token, "access")
    assert "Invalid token" in str(exc_info.value.detail)


@pytest.mark.anyio
async def test_get_subject_for_token_type_missing_subject(registered_user):
    token = security.jwt.encode(
        {"type": "access", "exp": 9999999999},
        security.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token(token, "access")
    assert "Token payload does not contain email" in str(exc_info.value.detail)


@pytest.mark.anyio
async def test_get_subject_for__wrong_token_type(registered_user):
    confirmation_token = security.create_confirmation_token(registered_user["email"])
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token(confirmation_token, "access")
    assert "Token is not a access token" in str(exc_info.value.detail)

    access_token = security.create_access_token(registered_user["email"])
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token(access_token, "confirmation")
    assert "Token is not a confirmation token" in str(exc_info.value.detail)
