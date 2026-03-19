import logging
from json import JSONDecodeError

import httpx
from databases import Database

from socialmediaapi.config import config
from socialmediaapi.database import post_table

logger = logging.getLogger(__name__)


class APIResponseErrorException(Exception):
    pass


async def send_simple_email(to_email: str, subject: str, body: str):
    logger.info(f"Sending email to {to_email} with subject '{subject}'")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://api.mailgun.net/v3/{config.MAILGUN_DOMAIN}/messages",
                auth=("api", config.MAILGUN_API_KEY),
                data={
                    "from": f"Excited User <mailgun@{config.MAILGUN_DOMAIN}>",
                    "to": [to_email],
                    "subject": subject,
                    "text": body,
                },
            )
            response.raise_for_status()
            logger.info(f"Email sent successfully to {to_email}")
            logger.debug(f"Email response: {response.content}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise APIResponseErrorException(
                f"API response failed with status code {e.response.status_code}"
            ) from e


async def send_welcome_email(to_email: str, confirmation_link: str):
    subject = "Welcome to Social Media API!"
    body = f"Thank you for signing up for our Social Media API. We're excited to have you on board! Please confirm your email by clicking the following link: {confirmation_link}"
    return await send_simple_email(to_email, subject, body)


async def _generate_cute_creature_api(prompt: str) -> str:
    logger.info(f"Generating cute creature image with prompt: {prompt}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.deepai.org/api/cute-creature-generator",
                headers={"api-key": config.DEEP_AI_API_KEY},
                data={"text": prompt},
                timeout=60,
            )
            logger.debug(f"Cute creature API response: {response.content}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to generate cute creature image: {e}")
            raise APIResponseErrorException(
                f"API response failed with status code {e.response.status_code}"
            ) from e
        except (JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse cute creature API response: {e}")
            raise APIResponseErrorException("Invalid API response format") from e


async def generate_and_add_to_post(
    email: str,
    post_id: int,
    post_url: str,
    database: Database,
    prompt: str = "A cute creature sitting on a post with a beautiful background",
):
    logger.info(
        f"Generating cute creature image for post {post_id} with prompt: {prompt}"
    )
    try:
        api_response = await _generate_cute_creature_api(prompt)
    except APIResponseErrorException:
        await send_simple_email(
            email,
            "Image Generation Failed",
            "Hi, we encountered an error while generating your image for your post. Please try again later.",
        )
    logger.debug("Connecting to database to add image URL to post")
    query = (
        post_table.update()
        .where(post_table.c.id == post_id)
        .values(image_url=api_response["output_url"])
    )
    logger.debug(f"Executing database query: {query}")
    await database.execute(query)
    logger.debug("Database connection closed in the background task")
    await send_simple_email(
        email,
        "Your Image is Ready!",
        f"Hi, your cute creature image for your post is ready! You can view it here: {post_url}",
    )
    return api_response
