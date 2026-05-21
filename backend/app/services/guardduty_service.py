"""GuardDuty integration — fetch threat-detection findings."""

import logging
from datetime import datetime, timezone

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
    return boto3.client("guardduty", **kwargs)


def get_detector_id() -> str | None:
    """Get the first available GuardDuty detector ID."""
    try:
        gd = _get_client()
        detectors = gd.list_detectors().get("DetectorIds", [])
        return detectors[0] if detectors else None
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Could not list GuardDuty detectors: %s", exc)
        return None


def get_guardduty_findings(limit: int = 10) -> list[dict]:
    """Fetch recent GuardDuty findings and format them as log entries."""
    detector_id = get_detector_id()
    if not detector_id:
        return []

    try:
        gd = _get_client()
        finding_ids_resp = gd.list_findings(
            DetectorId=detector_id,
            MaxResults=min(limit, 50),
            SortCriteria={"AttributeName": "updatedAt", "OrderBy": "DESC"},
        )
        finding_ids = finding_ids_resp.get("FindingIds", [])
        if not finding_ids:
            return []

        findings_resp = gd.get_findings(
            DetectorId=detector_id,
            FindingIds=finding_ids,
        )
        return [_format_finding(f) for f in findings_resp.get("Findings", [])]
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Failed to fetch GuardDuty findings: %s", exc)
        return []


def _format_finding(finding: dict) -> dict:
    """Convert a raw GuardDuty finding into a frontend-compatible log entry."""
    severity = finding.get("Severity", 0)
    if severity >= 7:
        sev_label = "danger"
    elif severity >= 4:
        sev_label = "warning"
    else:
        sev_label = "info"

    updated = finding.get("UpdatedAt", "")
    if isinstance(updated, datetime):
        updated = updated.isoformat()

    return {
        "id": f"gd-{finding.get('Id', '')[:12]}",
        "service": "GuardDuty",
        "type": finding.get("Type", "Finding"),
        "message": finding.get("Description", finding.get("Title", "No description")),
        "severity": sev_label,
        "time": updated,
    }
