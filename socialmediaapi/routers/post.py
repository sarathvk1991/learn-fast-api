import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from socialmediaapi.database import comment_table, database, like_table, post_table
from socialmediaapi.models.post import (
    Comment,
    CommentIn,
    PostLike,
    PostLikeIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
    UserPostWithLikes,
)
from socialmediaapi.models.user import User
from socialmediaapi.security import get_current_user
from socialmediaapi.tasks import generate_and_add_to_post

router = APIRouter()

logger = logging.getLogger(__name__)

select_post_and_likes_query = (
    sqlalchemy.select(
        post_table,
        sqlalchemy.func.count(like_table.c.id).label("likes"),
    )
    .select_from(
        post_table.outerjoin(like_table, post_table.c.id == like_table.c.post_id)
    )
    .group_by(post_table.c.id)
)


class PostSortBy(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"


@router.get("/posts", response_model=list[UserPostWithLikes])
async def get_posts(sorting: PostSortBy = PostSortBy.new):
    logger.info("Fetching all posts")
    if sorting == PostSortBy.new:
        query = select_post_and_likes_query.order_by(sqlalchemy.desc(post_table.c.id))
    elif sorting == PostSortBy.old:
        query = select_post_and_likes_query.order_by(post_table.c.id.asc())
    elif sorting == PostSortBy.most_likes:
        query = select_post_and_likes_query.order_by(sqlalchemy.desc("likes"))
    else:
        query = select_post_and_likes_query

    logger.debug("Query: %s", query)
    return await database.fetch_all(query)


@router.post("/posts", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn,
    current_user: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    request: Request,
    prompt: str = None,
):
    logger.info("Creating a new post")

    data = {**post.model_dump(), "user_id": current_user.id}
    query = post_table.insert().values(**data)
    logger.debug("Query: %s", query)
    post_id = await database.execute(query)
    if prompt:
        background_tasks.add_task(
            generate_and_add_to_post,
            current_user.email,
            post_id,
            request.url_for("get_post_with_comments", post_id=post_id),
            database,
            prompt,
        )
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
    query = select_post_and_likes_query.where(post_table.c.id == post_id)
    logger.debug("Query: %s", query)
    post = await database.fetch_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return UserPostWithComments(
        post=post, comments=await get_comments_for_post(post_id)
    )


async def find_post(post_id: int) -> UserPost:
    logger.debug("Finding post with id=%d", post_id)
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug("Query: %s", query)
    post = await database.fetch_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("/likes/", response_model=PostLike, status_code=201)
async def like_post(
    like: PostLikeIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Liking post_id=%d by user_id=%d", like.post_id, current_user.id)
    post = await find_post(like.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    data = {**like.model_dump(), "user_id": current_user.id}
    query = like_table.insert().values(**data)
    logger.debug("Query: %s", query)
    like_id = await database.execute(query)
    return {**data, "id": like_id}
