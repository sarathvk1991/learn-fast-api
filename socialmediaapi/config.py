from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class GlobalConfig(BaseConfig):
    DATABASE_URL: Optional[str] = None
    DB_FORCE_ROLLBACK: bool = False
    LOGTAIL_TOKEN: Optional[str] = None
    MAILGUN_API_KEY: Optional[str] = None
    MAILGUN_DOMAIN: Optional[str] = None
    B2_KEY_ID: Optional[str] = None
    B2_APPLICATION_KEY: Optional[str] = None
    B2_BUCKET_NAME: Optional[str] = None

    # config: ClassVar[BaseConfig] = BaseConfig()


class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="DEV_")


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="PROD_")


class TestConfig(GlobalConfig):
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    DB_FORCE_ROLLBACK: bool = True

    model_config = SettingsConfigDict(env_prefix="TEST_")


@lru_cache()
def get_config() -> GlobalConfig:
    env_state = BaseConfig().ENV_STATE
    if env_state == "dev":
        return DevConfig()
    elif env_state == "prod":
        return ProdConfig()
    elif env_state == "test":
        return TestConfig()
    else:
        raise ValueError(f"Invalid ENV_STATE: {env_state}")


config = get_config()
