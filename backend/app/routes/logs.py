"""Logs endpoint — aggregates CloudWatch, GuardDuty, and CloudTrail events."""

import logging

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.services.cloudtrail_service import get_recent_trail_events
from app.services.cloudwatch_service import get_recent_logs
from app.services.guardduty_service import get_guardduty_findings

router = APIRouter(tags=["Logs"])
logger = logging.getLogger(__name__)


@router.get("/logs")
async def get_logs(user: dict = Depends(get_current_user)) -> dict:
    """Aggregate logs from CloudWatch, GuardDuty findings, and CloudTrail events."""
    all_logs = []

    # CloudWatch logs
    try:
        all_logs.extend(get_recent_logs(limit=15))
    except Exception as exc:
        logger.warning("CloudWatch log fetch failed: %s", exc)

    # GuardDuty findings
    try:
        all_logs.extend(get_guardduty_findings(limit=5))
    except Exception as exc:
        logger.warning("GuardDuty fetch failed: %s", exc)

    # CloudTrail events
    try:
        all_logs.extend(get_recent_trail_events(limit=5))
    except Exception as exc:
        logger.warning("CloudTrail fetch failed: %s", exc)

    # Sort by time descending
    all_logs.sort(key=lambda x: x.get("time", ""), reverse=True)

    return {"logs": all_logs[:20]}
