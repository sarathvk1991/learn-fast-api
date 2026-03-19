import ssl

import databases
import sqlalchemy

from socialmediaapi.config import config

metadata = sqlalchemy.MetaData()

post_table = sqlalchemy.Table(
    "posts",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.String(length=255)),
    sqlalchemy.Column(
        "user_id",
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("users.id"),
        nullable=False,
    ),
    sqlalchemy.Column("image_url", sqlalchemy.String),
)

user_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String(length=255), unique=True),
    sqlalchemy.Column("password", sqlalchemy.String(length=255)),
    sqlalchemy.Column("confirmed", sqlalchemy.Boolean, default=False),
)

comment_table = sqlalchemy.Table(
    "comments",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(
        "post_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("posts.id"), nullable=False
    ),
    sqlalchemy.Column("body", sqlalchemy.String(length=255)),
    sqlalchemy.Column(
        "user_id",
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("users.id"),
        nullable=False,
    ),
)

like_table = sqlalchemy.Table(
    "likes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(
        "post_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("posts.id"), nullable=False
    ),
    sqlalchemy.Column(
        "user_id",
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("users.id"),
        nullable=False,
    ),
)

DATABASE_URL = config.DATABASE_URL

# Convert async URL -> sync URL for table creation
if DATABASE_URL.startswith("mysql+aiomysql"):
    SYNC_DATABASE_URL = DATABASE_URL.replace("+aiomysql", "+pymysql")
elif DATABASE_URL.startswith("sqlite+aiosqlite"):
    SYNC_DATABASE_URL = DATABASE_URL.replace("+aiosqlite", "")
else:
    SYNC_DATABASE_URL = DATABASE_URL

engine = sqlalchemy.create_engine(SYNC_DATABASE_URL)

# metadata.create_all(engine)

# database = databases.Database(DATABASE_URL, force_rollback=config.DB_FORCE_ROLLBACK)

ssl_context = None

db_kwargs = {
    "force_rollback": config.DB_FORCE_ROLLBACK,
}

# ✅ Only apply SSL for MySQL (prod)
if DATABASE_URL.startswith("mysql+aiomysql") and config.ENV_STATE == "prod":
    ssl_context = ssl.create_default_context()
    db_kwargs["ssl"] = ssl_context

database = databases.Database(
    DATABASE_URL,
    **db_kwargs,
)
