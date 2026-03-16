import databases
import sqlalchemy

from socialmediaapi.config import config

metadata = sqlalchemy.MetaData()

post_table = sqlalchemy.Table(
    "posts",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.String(length=255)),
)

comment_table = sqlalchemy.Table(
    "comments",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(
        "post_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("posts.id"), nullable=False
    ),
    sqlalchemy.Column("body", sqlalchemy.String(length=255)),
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

metadata.create_all(engine)

database = databases.Database(DATABASE_URL, force_rollback=config.DB_FORCE_ROLLBACK)
