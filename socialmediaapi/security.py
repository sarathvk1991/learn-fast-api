import datetime
import logging
from typing import Annotated, Literal

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from socialmediaapi.database import database, user_table

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"])

SECRET_KEY = "123jj1o1hihnuhaiugduisahdiuh0kka"

ALGORITHM = "HS256"

oauth2scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def access_token_expires_in() -> int:
    return 30


def confirm_token_expires_in() -> int:
    return 1440


def create_access_token(email: str):
    logger.debug(f"Creating access token for email: {email}")
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        access_token_expires_in()
    )
    jwt_payload = {"sub": email, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(jwt_payload, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_confirmation_token(email: str):
    logger.debug(f"Creating confirmation token for email: {email}")
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirm_token_expires_in()
    )
    jwt_payload = {"sub": email, "exp": expire, "type": "confirmation"}
    encoded_jwt = jwt.encode(jwt_payload, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_subject_for_token(
    token: str, token_type: Literal["access", "confirmation"]
) -> str:
    logger.debug("Decoding access token")
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError as e:
        logger.warning("Token has expired")
        raise create_credentials_exception("Token has expired") from e
    except JWTError as e:
        logger.warning("Invalid token")
        raise create_credentials_exception("Invalid token") from e
    email: str = payload.get("sub")
    if email is None:
        logger.warning("Token payload does not contain email")
        raise create_credentials_exception("Token payload does not contain email")
    type_ = payload.get("type")
    if type_ is None or type_ != token_type:
        logger.warning(f"Token is not a {token_type} token")
        raise create_credentials_exception(f"Token is not a {token_type} token")
    return email


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
        raise create_credentials_exception("Authentication failed: user not found")
    if not verify_password(password, user.password):
        logger.warning("Authentication failed: incorrect password")
        raise create_credentials_exception("Authentication failed: incorrect password")
    logger.info("Authentication successful")
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2scheme)]):
    email = get_subject_for_token(token, "access")
    user = await get_user(email)
    if user is None:
        logger.warning("User not found for email in token")
        raise create_credentials_exception("User not found for email in token")
    logger.info(f"Current user: {user['email']}")
    return user
