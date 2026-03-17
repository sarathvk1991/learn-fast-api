import pytest
from httpx import AsyncClient

from socialmediaapi import security


async def create_post(
    body: str, async_client: AsyncClient, logged_in_token: str
) -> dict:
    headers = {"Authorization": f"Bearer {logged_in_token}"}
    response = await async_client.post("/posts/", json={"body": body}, headers=headers)
    return response.json()


async def create_comment(
    body: str, post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    headers = {"Authorization": f"Bearer {logged_in_token}"}
    response = await async_client.post(
        "/comments/", json={"body": body, "post_id": post_id}, headers=headers
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str) -> dict:
    return await create_post(
        body="This is a test post",
        async_client=async_client,
        logged_in_token=logged_in_token,
    )


@pytest.fixture()
async def created_comment(
    created_post: dict, async_client: AsyncClient, logged_in_token: str
):
    return await create_comment(
        body="This is a test comment",
        post_id=created_post["id"],
        async_client=async_client,
        logged_in_token=logged_in_token,
    )


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient, logged_in_token: str):
    name = "This is a test post"
    headers = {"Authorization": f"Bearer {logged_in_token}"}
    response = await async_client.post("/posts/", json={"body": name}, headers=headers)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["body"] == name
    assert isinstance(response_json["id"], int)


@pytest.mark.anyio
async def test_create_post_with_no_body(
    async_client: AsyncClient, logged_in_token: str
):
    headers = {"Authorization": f"Bearer {logged_in_token}"}
    response = await async_client.post("/posts/", json={}, headers=headers)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_getall_posts(created_post: dict, async_client: AsyncClient):
    response = await async_client.get("/posts/")
    assert response.status_code == 200
    assert created_post in response.json()


@pytest.mark.anyio
async def test_create_comment(
    created_post: dict, async_client: AsyncClient, logged_in_token: str
):
    name = "This is a test comment"
    headers = {"Authorization": f"Bearer {logged_in_token}"}

    response = await async_client.post(
        "/comments/",
        json={"body": name, "post_id": created_post["id"]},
        headers=headers,
    )
    response_json = response.json()

    assert response.status_code == 201
    assert response_json["body"] == name
    assert response_json["post_id"] == created_post["id"]
    assert isinstance(response_json["id"], int)


@pytest.mark.anyio
async def test_create_comment_with_no_body(
    created_post: dict, async_client: AsyncClient, logged_in_token: str
):
    headers = {"Authorization": f"Bearer {logged_in_token}"}
    response = await async_client.post(
        "/comments/", json={"post_id": created_post["id"]}, headers=headers
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_comment_with_no_post_id(
    async_client: AsyncClient, logged_in_token: str
):
    headers = {"Authorization": f"Bearer {logged_in_token}"}
    response = await async_client.post(
        "/comments/", json={"body": "This is a test comment"}, headers=headers
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_comments_by_post_id(
    created_comment: dict, async_client: AsyncClient
):
    response = await async_client.get(f"/posts/{created_comment['post_id']}/comments/")
    assert response.status_code == 200
    assert created_comment in response.json()


@pytest.mark.anyio
async def test_get_comments_by_post_id_with_no_comments(
    created_post: dict, async_client: AsyncClient
):
    response = await async_client.get(f"/posts/{created_post['id']}/comments/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_comments_by_post_id_with_invalid_post_id(async_client: AsyncClient):
    response = await async_client.get("/posts/999/comments/")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient, registered_user, mocker
):
    # Create a token that expires immediately
    mocker.patch("socialmediaapi.security.access_token_expires_in", return_value=-1)
    expired_token = security.create_access_token(registered_user["email"])

    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await async_client.post(
        "/posts/", json={"body": "Test post"}, headers=headers
    )
    assert response.status_code == 401
