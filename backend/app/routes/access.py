"""Secure access endpoint — generates S3 pre-signed URLs for time-limited downloads."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user
from app.services.cloudwatch_service import put_log_event
from app.services.dynamodb_service import get_file_metadata
from app.services.s3_service import generate_presigned_url

router = APIRouter(tags=["Access"])
logger = logging.getLogger(__name__)


@router.get("/access")
async def get_secure_access(
    fileId: str = Query(...),
    user: dict = Depends(get_current_user),
) -> dict:
    file_meta = None
    try:
        file_meta = get_file_metadata(fileId)
    except Exception as exc:
        logger.warning("DynamoDB lookup failed: %s", exc)

    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        signed_url = generate_presigned_url(file_meta["s3_key"], expires_in=300)
    except Exception as exc:
        logger.exception("Failed to generate presigned URL")
        raise HTTPException(status_code=500, detail=f"Could not generate URL: {exc}") from exc

    put_log_event(
        "S3", "Pre-signed URL generated",
        f"URL generated for {file_meta['filename']} by {user.get('email')}",
        "success",
    )

    return {
        "signedUrl": signed_url,
        "expiresIn": "5 minutes",
        "message": "Temporary pre-signed URL generated.",
    }
