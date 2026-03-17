import logging

from fastapi import APIRouter, HTTPException

from socialmediaapi.database import database, user_table
from socialmediaapi.models.user import UserIn
from socialmediaapi.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=201)
async def register_user(user: UserIn):
    if await get_user(user.email):
        raise HTTPException(
            status_code=400, detail="A user with this email already exists"
        )
    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=hashed_password)
    logger.debug(f"Executing query: {query}")
    await database.execute(query)
    return {"message": "User registered successfully"}


@router.post("/token")
async def login_user(user: UserIn):
    user = await authenticate_user(user.email, user.password)
    access_token = create_access_token(email=user["email"])
    return {"access_token": access_token, "token_type": "bearer"}
