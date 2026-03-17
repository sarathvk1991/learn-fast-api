import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from socialmediaapi.database import comment_table, database, post_table
from socialmediaapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)
from socialmediaapi.models.user import User
from socialmediaapi.security import get_current_user

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/posts/", response_model=list[UserPost])
async def get_posts():
    logger.info("Fetching all posts")
    query = post_table.select()
    logger.debug("Query: %s", query)
    return await database.fetch_all(query)


@router.post("/posts/", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Creating a new post")

    data = {**post.model_dump(), "user_id": current_user.id}
    query = post_table.insert().values(**data)
    logger.debug("Query: %s", query)
    post_id = await database.execute(query)
    return {**data, "id": post_id}


@router.post("/comments/", response_model=Comment, status_code=201)
async def create_comment(
    comment: CommentIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Creating a new comment for post_id=%d", comment.post_id)

    await find_post(comment.post_id)
    data = {**comment.model_dump(), "user_id": current_user.id}
    query = comment_table.insert().values(**data)
    logger.debug("Query: %s", query)
    comment_id = await database.execute(query)
    return {**data, "id": comment_id}


@router.get("/posts/{post_id}/comments/", response_model=list[Comment])
async def get_comments_for_post(post_id: int):
    logger.info("Fetching comments for post_id=%d", post_id)
    await find_post(post_id)
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    logger.debug("Query: %s", query)
    return await database.fetch_all(query)


@router.get("/posts/{post_id}/", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    logger.info("Fetching post with comments for post_id=%d", post_id)
    post = await find_post(post_id)
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    logger.debug("Query: %s", query)
    comments = await database.fetch_all(query)
    return UserPostWithComments(post=post, comments=comments)


async def find_post(post_id: int) -> UserPost:
    logger.debug("Finding post with id=%d", post_id)
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug("Query: %s", query)
    post = await database.fetch_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
