import logging

import httpx

from socialmediaapi.config import config

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
