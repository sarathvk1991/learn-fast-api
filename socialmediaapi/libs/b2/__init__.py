import logging
from functools import lru_cache

import b2sdk.v2 as b2

from socialmediaapi.config import config

logger = logging.getLogger(__name__)


@lru_cache()
def b2_api():
    logger.info("Initializing B2 API client")
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)
    b2_api.authorize_account("production", config.B2_KEY_ID, config.B2_APPLICATION_KEY)
    return b2_api


@lru_cache()
def b2_get_bucket(api: b2.B2Api):
    logger.info(f"Retrieving B2 bucket: {config.B2_BUCKET_NAME}")
    bucket = api.get_bucket_by_name(config.B2_BUCKET_NAME)
    return bucket


def b2_upload_file(local_file: str, file_name: str):
    api = b2_api()
    logger.info(f"Uploading file to B2: {local_file} as {file_name}")
    uploaded_file = b2_get_bucket(api).upload_local_file(
        local_file=local_file,
        file_name=file_name,
    )

    download_url = api.get_download_url_for_file_id(uploaded_file.file_id_)
    logger.info(
        f"File uploaded to B2 with file_id: {uploaded_file.file_id_}, download_url: {download_url}"
    )
    return download_url
