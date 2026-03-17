import datetime
import logging

from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext

from socialmediaapi.database import database, user_table

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"])

SECRET_KEY = "123jj1o1hihnuhaiugduisahdiuh0kka"

ALGORITHM = "HS256"

credentials_exception = HTTPException(
    status_code=401, detail="Could not validate credentials"
)


def access_token_expires_in() -> int:
    return 30


def create_access_token(email: str):
    logger.debug(f"Creating access token for email: {email}")
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        access_token_expires_in()
    )
    jwt_payload = {"sub": email, "exp": expire}
    encoded_jwt = jwt.encode(jwt_payload, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


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


async def authenticate_user(email: str, password: str):
    logger.debug(f"Authenticating user with email: {email}")
    user = await get_user(email)
    if not user:
        logger.warning("Authentication failed: user not found")
        raise credentials_exception
    if not verify_password(password, user.password):
        logger.warning("Authentication failed: incorrect password")
        raise credentials_exception
    logger.info("Authentication successful")
    return user
