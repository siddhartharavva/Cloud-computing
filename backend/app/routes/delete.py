"""Delete endpoint — removes files from S3 and marks metadata expired in DynamoDB."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.services.cloudwatch_service import put_log_event
from app.services.dynamodb_service import get_file_metadata, delete_file_metadata
from app.services.s3_service import delete_s3_object
from app.services.sqs_service import send_file_deleted_event

router = APIRouter(tags=["Delete"])
logger = logging.getLogger(__name__)


@router.delete("/delete/{file_id}")
async def delete_file_route(
    file_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    file_meta = None
    try:
        file_meta = get_file_metadata(file_id)
    except Exception as exc:
        logger.warning("DynamoDB lookup failed: %s", exc)

    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found.")

    if file_meta.get("owner") != user.get("email"):
        raise HTTPException(status_code=403, detail="Only the uploader can delete this file.")

    # Delete from S3
    try:
        delete_s3_object(file_meta["s3Key"])
    except Exception as exc:
        logger.exception("S3 delete failed")
        raise HTTPException(status_code=500, detail=f"S3 delete failed: {exc}") from exc

    # Delete from DynamoDB
    try:
        delete_file_metadata(file_id)
    except Exception as exc:
        logger.warning("Failed to delete file metadata in DynamoDB: %s", exc)

    # CloudWatch log
    put_log_event(
        "S3", "File deleted",
        f"{file_meta.get('fileName', 'unknown')} deleted by {user.get('email')}",
        "warning",
    )

    # SQS event
    send_file_deleted_event(file_id, file_meta.get("fileName", ""), user.get("email", "unknown"))

    return {"message": "File deleted from S3 and metadata marked expired."}
