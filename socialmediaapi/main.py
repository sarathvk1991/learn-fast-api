import logging
from contextlib import asynccontextmanager

import sentry_sdk
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler

from socialmediaapi.config import config
from socialmediaapi.database import database
from socialmediaapi.logging_conf import configure_logging
from socialmediaapi.routers.post import router as post_router
from socialmediaapi.routers.upload import router as upload_router
from socialmediaapi.routers.user import router as user_router

sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(post_router)
app.include_router(user_router)
app.include_router(upload_router)


@app.exception_handler(HTTPException)
async def http_exception_handler_logging(request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.status_code} - {exc.detail}")
    return await http_exception_handler(request, exc)


@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
    return {"result": division_by_zero}
