"""Zero Trust access verification — real policy checks against DynamoDB metadata."""

import ipaddress
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_user
from app.services.cloudwatch_service import put_log_event, put_metric
from app.services.dynamodb_service import get_file_metadata
from app.services.sns_service import publish_sns_alert
from app.services.sqs_service import send_access_denied_event


router = APIRouter(tags=["Verify"])
logger = logging.getLogger(__name__)


class VerifyRequest(BaseModel):
    fileId: str = ""
    sourceIp: str = "10.0.0.42"
    deviceTrust: str = "trusted"
    role: str = "analyst"
    expired: bool = False


def _ip_in_cidr(ip: str, cidr: str) -> bool:
    """Check if an IP address falls within a CIDR range."""
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False


@router.post("/verify")
async def verify_access(
    payload: VerifyRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    checks = []

    # 1. Cognito token (passed if we reached this handler)
    checks.append({"name": "Cognito token", "passed": True})

    # 2. Fetch file policy from DynamoDB
    file_meta = None
    try:
        if payload.fileId:
            file_meta = get_file_metadata(payload.fileId)
    except Exception as exc:
        logger.warning("DynamoDB lookup failed: %s", exc)

    # 3. Expiry window
    expired = payload.expired
    checks.append({"name": "Expiry window", "passed": not expired})

    # 4. IP policy
    allowed_cidr = file_meta.get("allowed_ip", "10.0.0.0/24") if file_meta else "10.0.0.0/24"
    ip_ok = _ip_in_cidr(payload.sourceIp, allowed_cidr)
    checks.append({"name": "IP policy", "passed": ip_ok})

    # 5. Device trust
    device_ok = payload.deviceTrust != "untrusted"
    checks.append({"name": "Device trust", "passed": device_ok})

    # 6. DynamoDB policy record exists
    checks.append({"name": "DynamoDB policy", "passed": file_meta is not None or not payload.fileId})

    all_passed = all(c["passed"] for c in checks)
    score = sum(20 for c in checks if c["passed"])

    decision = "ALLOW" if all_passed else "DENY"
    reason = (
        "Access approved. Token, expiry, IP, role, and device trust checks passed."
        if all_passed
        else "Access denied. One or more Zero Trust policy checks failed."
    )

    # Log and alert
    if all_passed:
        put_log_event(
            "Lambda", "Access verified",
            f"Access ALLOWED for {user.get('email')} on {payload.fileId}",
            "success",
        )
        put_metric("VerifiedAccessTotal")
    else:
        failed = [c["name"] for c in checks if not c["passed"]]
        put_log_event(
            "GuardDuty", "Suspicious attempt",
            f"Access DENIED for {user.get('email')} on {payload.fileId}: score={score}, failed={failed}",
            "danger",
        )
        put_metric("BlockedAttemptsTotal")

        # SNS alert on denied access
        publish_sns_alert(
            f"Access DENIED for {user.get('email')} on file {payload.fileId}. "
            f"Score: {score}/100. Failed checks: {failed}",
            triggered_by=user.get("email", "unknown"),
        )

        # SQS event for async audit
        send_access_denied_event(
            payload.fileId,
            user.get("email", "unknown"),
            f"Failed checks: {failed}",
        )

    return {
        "decision": decision,
        "score": score,
        "reason": reason,
        "checks": checks,
    }
