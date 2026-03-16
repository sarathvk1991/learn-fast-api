import pytest
from httpx import AsyncClient


async def create_post(body: str, async_client: AsyncClient) -> dict:
    response = await async_client.post("/posts/", json={"body": body})
    return response.json()


async def create_comment(body: str, post_id: int, async_client: AsyncClient) -> dict:
    response = await async_client.post(
        "/comments/", json={"body": body, "post_id": post_id}
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient):
    return await create_post("This is a test post", async_client)


@pytest.fixture()
async def created_comment(created_post: dict, async_client: AsyncClient):
    return await create_comment(
        "This is a test comment", created_post["id"], async_client
    )


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient):
    name = "This is a test post"

    response = await async_client.post("/posts/", json={"body": name})
    assert response.status_code == 201
    assert {"id": 1, "body": name}.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_with_no_body(async_client: AsyncClient):
    response = await async_client.post("/posts/", json={})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_getall_posts(created_post: dict, async_client: AsyncClient):
    response = await async_client.get("/posts/")
    assert response.status_code == 200
    assert created_post in response.json()


@pytest.mark.anyio
async def test_create_comment(created_post: dict, async_client: AsyncClient):
    name = "This is a test comment"

    response = await async_client.post(
        "/comments/", json={"body": name, "post_id": created_post["id"]}
    )
    assert response.status_code == 201
    assert {
        "id": 1,
        "body": name,
        "post_id": created_post["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_comment_with_no_body(
    created_post: dict, async_client: AsyncClient
):
    response = await async_client.post(
        "/comments/", json={"post_id": created_post["id"]}
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_comment_with_no_post_id(async_client: AsyncClient):
    response = await async_client.post(
        "/comments/", json={"body": "This is a test comment"}
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
