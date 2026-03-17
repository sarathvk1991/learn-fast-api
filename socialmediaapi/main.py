import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler

from socialmediaapi.database import database
from socialmediaapi.logging_conf import configure_logging
from socialmediaapi.routers.post import router as post_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)
app.include_router(post_router)


@app.exception_handler(HTTPException)
async def http_exception_handler_logging(request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.status_code} - {exc.detail}")
    return await http_exception_handler(request, exc)
