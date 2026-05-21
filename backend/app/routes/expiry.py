"""Expiry scan endpoint — cleans up files past their expiry window."""

import logging

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.services.cloudwatch_service import put_log_event, put_metric
from app.services.dynamodb_service import get_expired_files, mark_file_expired
from app.services.s3_service import delete_s3_object

router = APIRouter(tags=["Expiry"])
logger = logging.getLogger(__name__)


@router.post("/admin/expiry-scan")
async def run_expiry_scan(
    user: dict = Depends(get_current_user),
) -> dict:
    """Manually trigger the same expiry logic the EventBridge Lambda runs on schedule."""
    try:
        expired_files = get_expired_files()
    except Exception as exc:
        logger.exception("Failed to scan for expired files")
        return {"message": f"Scan failed: {exc}", "expired_count": 0}

    cleaned = 0
    for f in expired_files:
        try:
            delete_s3_object(f["s3Key"])
            mark_file_expired(f["fileId"])
            cleaned += 1
        except Exception as exc:
            logger.warning("Failed to clean up file %s: %s", f.get("fileId"), exc)

    put_log_event(
        "EventBridge", "Lifecycle check",
        f"Scheduled expiry scan executed. Cleaned {cleaned} file(s).",
        "warning",
    )
    put_metric("ExpiredFilesCleaned", float(cleaned))

    return {"message": f"Expired {cleaned} file(s).", "expired_count": cleaned}
