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


async def like_post(
    post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    headers = {"Authorization": f"Bearer {logged_in_token}"}
    response = await async_client.post(
        "/likes/", json={"post_id": post_id}, headers=headers
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
async def test_create_post(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token: str
):
    name = "This is a test post"
    headers = {"Authorization": f"Bearer {logged_in_token}"}
    response = await async_client.post("/posts/", json={"body": name}, headers=headers)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["body"] == name
    assert isinstance(response_json["id"], int)
    assert response_json["user_id"] == confirmed_user["id"]


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
    assert created_post["body"] == response.json()[0]["body"]


@pytest.mark.anyio
async def test_create_comment(
    created_post: dict,
    async_client: AsyncClient,
    confirmed_user: dict,
    logged_in_token: str,
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
    assert response_json["user_id"] == confirmed_user["id"]
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
    async_client: AsyncClient, confirmed_user: dict, mocker
):
    # Create a token that expires immediately
    mocker.patch("socialmediaapi.security.access_token_expires_in", return_value=-1)
    expired_token = security.create_access_token(confirmed_user["email"])
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await async_client.post(
        "/posts/", json={"body": "Test post"}, headers=headers
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_like_post(
    created_post: dict, async_client: AsyncClient, logged_in_token: str
):
    response = await like_post(
        post_id=created_post["id"],
        async_client=async_client,
        logged_in_token=logged_in_token,
    )
    assert response["post_id"] == created_post["id"]
    assert isinstance(response["id"], int)
    assert response["user_id"] is not None


@pytest.mark.anyio
async def test_get_post_with_comments(
    created_comment: dict, async_client: AsyncClient, created_post: dict
):
    response = await async_client.get(f"/posts/{created_post['id']}/")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["post"]["id"] == created_post["id"]
    assert response_json["post"]["body"] == created_post["body"]
    assert response_json["post"]["user_id"] == created_post["user_id"]
    assert len(response_json["comments"]) == 1
    comment = response_json["comments"][0]
    assert comment["id"] == created_comment["id"]
    assert comment["body"] == created_comment["body"]
    assert comment["post_id"] == created_comment["post_id"]
    assert comment["user_id"] == created_comment["user_id"]
    assert response_json["post"]["likes"] == 0


@pytest.mark.anyio
@pytest.mark.parametrize("sorting, expected_order", [("old", [1, 2]), ("new", [2, 1])])
async def test_get_all_posts_sorted(
    created_post: dict,
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
):
    # Create another post to ensure we have multiple posts
    await create_post(
        body="This is another test post",
        async_client=async_client,
        logged_in_token=logged_in_token,
    )

    response = await async_client.get("/posts/", params={"sorting": sorting})
    assert response.status_code == 200
    posts = response.json()
    assert len(posts) >= 2
    # Check if the posts are sorted by id in the expected order
    assert posts[0]["id"] == expected_order[0]
    assert posts[1]["id"] == expected_order[1]


@pytest.mark.anyio
async def test_get_all_posts_sorted_by_likes(
    created_post: dict, async_client: AsyncClient, logged_in_token: str
):
    # Create another post to ensure we have multiple posts
    another_post = await create_post(
        body="This is another test post",
        async_client=async_client,
        logged_in_token=logged_in_token,
    )

    # Like the first post twice and the second post once
    await like_post(
        post_id=created_post["id"],
        async_client=async_client,
        logged_in_token=logged_in_token,
    )
    await like_post(
        post_id=created_post["id"],
        async_client=async_client,
        logged_in_token=logged_in_token,
    )
    await like_post(
        post_id=another_post["id"],
        async_client=async_client,
        logged_in_token=logged_in_token,
    )

    response = await async_client.get("/posts/", params={"sorting": "most_likes"})
    assert response.status_code == 200
    posts = response.json()
    assert len(posts) >= 2
    # Check if the posts are sorted by likes in descending order
    assert posts[0]["likes"] >= posts[1]["likes"]
