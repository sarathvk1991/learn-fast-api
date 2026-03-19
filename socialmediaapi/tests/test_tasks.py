import httpx
import pytest

from socialmediaapi.tasks import APIResponseErrorException, send_simple_email


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
