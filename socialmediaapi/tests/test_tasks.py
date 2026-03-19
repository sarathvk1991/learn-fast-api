import httpx
import pytest

from socialmediaapi.database import post_table
from socialmediaapi.tasks import (
    APIResponseErrorException,
    _generate_cute_creature_api,
    generate_and_add_to_post,
    send_simple_email,
)


@pytest.mark.anyio
async def test_send_simple_email(mock_httpx_client):
    await send_simple_email("test.example.com", "Test Subject", "Test Body")
    mock_httpx_client.post.assert_called()


@pytest.mark.anyio
async def test_send_simple_email_api_error(mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=500, content="", request=httpx.Request("POST", "//")
    )
    with pytest.raises(APIResponseErrorException) as exc_info:
        await send_simple_email("test.example.com", "Test Subject", "Test Body")
    assert "API response failed with status code 500" in str(exc_info.value)


@pytest.mark.anyio
async def test_generate_and_add_to_post(mock_httpx_client):
    json_response = {"output_url": "https://example.com/cute-creature.jpg"}
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200, json=json_response, request=httpx.Request("POST", "//")
    )
    result = await _generate_cute_creature_api(
        "A cute creature sitting on a post with a beautiful background"
    )
    assert result == json_response


@pytest.mark.anyio
async def test_generate_image_error(mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=500, content="", request=httpx.Request("POST", "//")
    )
    with pytest.raises(
        APIResponseErrorException, match="API response failed with status code 500"
    ):
        await _generate_cute_creature_api(
            "A cute creature sitting on a post with a beautiful background"
        )


@pytest.mark.anyio
async def test_generate_image_invalid_content(mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200, content="NOT JSON", request=httpx.Request("POST", "//")
    )
    with pytest.raises(APIResponseErrorException, match="Invalid API response format"):
        await _generate_cute_creature_api(
            "A cute creature sitting on a post with a beautiful background"
        )


@pytest.mark.anyio
async def test_generate_image_and_add_to_post(
    mock_httpx_client, created_post: dict, confirmed_user: dict, db
):
    json_response = {"output_url": "https://example.com/cute-creature.jpg"}
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200, json=json_response, request=httpx.Request("POST", "//")
    )
    await generate_and_add_to_post(
        email=confirmed_user["email"],
        post_id=created_post["id"],
        post_url="/posts/1",
        database=db,
        prompt="A cute creature sitting on a post with a beautiful background",
    )
    query = post_table.select().where(post_table.c.id == created_post["id"])
    updated_post = await db.fetch_one(query)
    assert updated_post["image_url"] == json_response["output_url"]
