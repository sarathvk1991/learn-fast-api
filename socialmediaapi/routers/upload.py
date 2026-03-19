import logging
import tempfile

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, status

from socialmediaapi.libs.b2 import b2_upload_file

logger = logging.getLogger(__name__)

router = APIRouter()

CHUNK_SIZE = 1024 * 1024  # 1MB


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
            logger.info(f"Saving uploaded file to temporary path: {temp_file_path}")
            async with aiofiles.open(temp_file_path, "wb") as out_file:
                while chunk := await file.read(CHUNK_SIZE):
                    await out_file.write(chunk)
            file_url = b2_upload_file(
                local_file=temp_file_path, file_name=file.filename
            )
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")
    return {
        "file_url": file_url,
        "detail": f"File uploaded successfully {file.filename}",
    }
