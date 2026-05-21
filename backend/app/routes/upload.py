import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.auth import get_current_user
from app.services.cloudwatch_service import put_log_event, put_metric
from app.services.dynamodb_service import save_file_metadata
from app.services.s3_service import S3ConfigurationError, S3UploadError, upload_file_to_s3
from app.services.sqs_service import send_upload_event


router = APIRouter(tags=["Upload"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=None)
async def upload_file(
    file: UploadFile = File(...),
    classification: str = Form("Confidential"),
    expiryHours: str = Form("24"),
    allowedIp: str = Form("10.0.0.0/24"),
    policy: str = Form("MFA + corporate IP + trusted device"),
    requireMfa: str = Form("true"),
    user: dict = Depends(get_current_user),
):
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={"error": "Uploaded file must include a filename."},
        )

    logger.info("Received upload request: filename=%s content_type=%s", file.filename, file.content_type)

    # Get file size before upload
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

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

    # Save metadata to DynamoDB
    try:
        save_file_metadata(
            file_id=result["file_id"],
            filename=result["filename"],
            s3_key=result["s3_key"],
            content_type=file.content_type,
            size_bytes=file_size,
            classification=classification,
            expiry_hours=int(expiryHours),
            allowed_ip=allowedIp,
            policy=policy,
            require_mfa=requireMfa.lower() == "true",
            owner=user.get("email", "unknown"),
        )
    except Exception as exc:
        logger.warning("DynamoDB save failed (upload still succeeded): %s", exc)

    # Log to CloudWatch
    put_log_event("S3", "File uploaded", f"{result['filename']} uploaded by {user.get('email')}", "success")
    put_metric("UploadsTotal")

    # Queue SQS event
    send_upload_event(result["file_id"], result["filename"], user.get("email", "unknown"))

    return {
        "message": "File uploaded successfully.",
        "filename": result["filename"],
        "file_id": result["file_id"],
        "s3_key": result["s3_key"],
    }
