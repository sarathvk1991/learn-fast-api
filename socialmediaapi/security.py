import logging

from socialmediaapi.database import database, user_table

logger = logging.getLogger(__name__)


async def get_user(email: str):
    logger.info(f"Fetching user from database with email: {email}")
    query = user_table.select().where(user_table.c.email == email)
    user = await database.fetch_one(query)
    if user:
        logger.info(f"User found: {user['email']}")
        return user
    else:
        logger.info("User not found")
        return None
