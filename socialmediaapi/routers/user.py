import logging

from fastapi import APIRouter, HTTPException, Request

import socialmediaapi.tasks as tasks
from socialmediaapi.database import database, user_table
from socialmediaapi.models.user import UserIn
from socialmediaapi.security import (
    authenticate_user,
    create_access_token,
    create_confirmation_token,
    get_password_hash,
    get_subject_for_token,
    get_user,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=201)
async def register_user(user: UserIn, request: Request):
    if await get_user(user.email):
        raise HTTPException(
            status_code=400, detail="A user with this email already exists"
        )
    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=hashed_password)
    logger.debug(f"Executing query: {query}")
    await database.execute(query)
    await tasks.send_welcome_email(
        user.email,
        confirmation_link=request.url_for(
            "confirm_user", token=create_confirmation_token(user.email)
        ),
    )
    return {
        "message": "User registered successfully. Please check your email to confirm your account."
    }


@router.post("/token")
async def login_user(user: UserIn):
    user = await authenticate_user(user.email, user.password)
    access_token = create_access_token(email=user["email"])
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirm/{token}")
async def confirm_user(token: str):
    # Logic to confirm the user using the token
    email = get_subject_for_token(token, "confirmation")
    user = await get_user(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )
    await database.execute(query)
    return {"detail": "User confirmed successfully"}
