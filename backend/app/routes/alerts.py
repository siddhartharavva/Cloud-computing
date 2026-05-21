"""Alerts endpoint — publish security alerts to SNS."""

import logging

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.services.cloudwatch_service import put_log_event
from app.services.sns_service import publish_sns_alert

router = APIRouter(tags=["Alerts"])
logger = logging.getLogger(__name__)


@router.post("/alerts/test")
async def trigger_test_alert(
    user: dict = Depends(get_current_user),
) -> dict:
    email = user.get("email", "unknown")
    sent = publish_sns_alert(
        f"Test security alert triggered by {email}. "
        "This is a demo alert from the Zero Trust platform.",
        triggered_by=email,
    )

    put_log_event(
        "SNS", "Alert sent",
        f"Test alert triggered by {email}",
        "warning",
    )

    if sent:
        return {"message": "SNS alert sent to the security notification topic."}
    return {"message": "SNS topic not configured. Alert logged locally."}
