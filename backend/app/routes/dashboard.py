"""Dashboard endpoint — aggregates DynamoDB metrics, files, and CloudWatch logs."""

import logging

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.services.cloudwatch_service import get_recent_logs
from app.services.dynamodb_service import get_dashboard_metrics, list_files

router = APIRouter(tags=["Dashboard"])
logger = logging.getLogger(__name__)


def _format_file_for_frontend(item: dict) -> dict:
    """Convert a DynamoDB item into the shape the React frontend expects."""
    size_bytes = item.get("size_bytes", 0)
    if isinstance(size_bytes, str):
        try:
            size_bytes = int(size_bytes)
        except ValueError:
            size_bytes = 0

    if size_bytes >= 1_048_576:
        size_str = f"{size_bytes / 1_048_576:.1f} MB"
    elif size_bytes >= 1024:
        size_str = f"{size_bytes / 1024:.0f} KB"
    else:
        size_str = f"{size_bytes} B"

    return {
        "id": item.get("fileId", ""),
        "name": item.get("fileName", "unknown"),
        "owner": item.get("owner", "unknown"),
        "size": size_str,
        "classification": item.get("classification", "Internal"),
        "status": item.get("status", "Active"),
        "expiry": item.get("expiryTime", ""),
        "storage": f"s3://bucket/{item.get('s3Key', '')}",
        "kmsKey": "alias/zt-file-exchange",
        "lastAccess": "via API",
        "policy": item.get("policy", ""),
    }


@router.get("/dashboard")
async def get_dashboard(user: dict = Depends(get_current_user)) -> dict:
    try:
        raw_files = list_files(limit=20)
        files = [_format_file_for_frontend(f) for f in raw_files]
    except Exception as exc:
        logger.warning("Failed to load files from DynamoDB: %s", exc)
        files = []

    try:
        metrics = get_dashboard_metrics()
    except Exception as exc:
        logger.warning("Failed to load metrics: %s", exc)
        metrics = {
            "totalFiles": 0, "verifiedAccess": 0, "blockedAttempts": 0,
            "expiringToday": 0, "avgVerificationMs": 0, "activePolicies": 0,
        }

    logs = get_recent_logs(limit=10)

    return {"metrics": metrics, "files": files, "logs": logs}
