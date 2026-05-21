"""CloudTrail integration — fetch audit trail events for S3 operations."""

import logging
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_client():
    settings = get_settings()
    kwargs = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }
    if settings.aws_session_token:
        kwargs["aws_session_token"] = settings.aws_session_token
    return boto3.client("cloudtrail", **kwargs)


def get_recent_trail_events(limit: int = 10) -> list[dict]:
    """Fetch recent CloudTrail events related to S3 operations."""
    try:
        ct = _get_client()
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)

        response = ct.lookup_events(
            LookupAttributes=[
                {
                    "AttributeKey": "EventSource",
                    "AttributeValue": "s3.amazonaws.com",
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=min(limit, 50),
        )
        return [_format_event(e) for e in response.get("Events", [])]
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Failed to fetch CloudTrail events: %s", exc)
        return []


def _format_event(event: dict) -> dict:
    """Convert a CloudTrail event into a frontend-compatible log entry."""
    event_time = event.get("EventTime", "")
    if isinstance(event_time, datetime):
        event_time = event_time.isoformat()

    event_name = event.get("EventName", "Unknown")

    # Classify by operation
    if event_name in ("PutObject", "CompleteMultipartUpload"):
        severity = "success"
        event_type = "Upload recorded"
    elif event_name in ("DeleteObject", "DeleteObjects"):
        severity = "warning"
        event_type = "Delete recorded"
    elif event_name in ("GetObject", "HeadObject"):
        severity = "info"
        event_type = "Access recorded"
    else:
        severity = "info"
        event_type = "Audit event"

    username = event.get("Username", "unknown")
    resources = event.get("Resources", [])
    resource_name = resources[0].get("ResourceName", "") if resources else ""

    return {
        "id": f"ct-{event.get('EventId', '')[:12]}",
        "service": "CloudTrail",
        "type": event_type,
        "message": f"{event_name} by {username}"
        + (f" on {resource_name}" if resource_name else ""),
        "severity": severity,
        "time": event_time,
    }
