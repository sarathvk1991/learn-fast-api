import pytest

from socialmediaapi import security


@pytest.mark.anyio
async def test_get_user(registered_user):
    user = await security.get_user(registered_user["email"])
    assert user is not None
    assert user["email"] == registered_user["email"]


@pytest.mark.anyio
async def test_get_nonexistent_user():
    user = await security.get_user("nonexistent@example.com")
    assert user is None
