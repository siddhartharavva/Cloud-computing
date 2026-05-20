from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.services.s3_service import S3ConfigurationError, S3UploadError, upload_file_to_s3


router = APIRouter(tags=["Upload"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict[str, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must include a filename.")

    try:
        result = await run_in_threadpool(
            upload_file_to_s3,
            file.file,
            file.filename,
            file.content_type,
        )
    except S3ConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except S3UploadError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "message": "File uploaded successfully.",
        "filename": result["filename"],
        "file_id": result["file_id"],
        "s3_key": result["s3_key"],
    }
