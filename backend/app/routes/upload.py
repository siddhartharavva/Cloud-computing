import logging

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.services.s3_service import S3ConfigurationError, S3UploadError, upload_file_to_s3


router = APIRouter(tags=["Upload"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=None)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={"error": "Uploaded file must include a filename."},
        )

    logger.info("Received upload request: filename=%s content_type=%s", file.filename, file.content_type)

    try:
        result = await run_in_threadpool(
            upload_file_to_s3,
            file.file,
            file.filename,
            file.content_type,
        )
    except S3ConfigurationError as exc:
        logger.exception("S3 configuration error")
        return JSONResponse(status_code=500, content={"error": str(exc)})
    except S3UploadError as exc:
        logger.exception("S3 upload error")
        return JSONResponse(status_code=502, content={"error": str(exc)})
    except Exception as exc:
        logger.exception("Unhandled upload route error")
        return JSONResponse(status_code=500, content={"error": f"Unexpected upload error: {exc}"})

    return {
        "message": "File uploaded successfully.",
        "filename": result["filename"],
        "file_id": result["file_id"],
        "s3_key": result["s3_key"],
    }
