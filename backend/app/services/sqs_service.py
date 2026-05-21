"""SQS integration — queue upload and security events for async processing."""

import json
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
    return boto3.client("sqs", **kwargs)


def send_event(event_type: str, payload: dict) -> bool:
    """Send an event message to the ZeroTrust SQS queue."""
    settings = get_settings()
    if not settings.sqs_queue_url:
        logger.debug("SQS_QUEUE_URL not configured; skipping event.")
        return False

    message = {
        "event_type": event_type,
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        sqs = _get_client()
        sqs.send_message(
            QueueUrl=settings.sqs_queue_url,
            MessageBody=json.dumps(message),
            MessageAttributes={
                "EventType": {
                    "DataType": "String",
                    "StringValue": event_type,
                },
            },
        )
        logger.info("Sent SQS event: %s", event_type)
        return True
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Failed to send SQS event: %s", exc)
        return False


def send_upload_event(file_id: str, filename: str, owner: str) -> bool:
    """Queue a file-upload event for async processing."""
    return send_event("FILE_UPLOADED", {
        "file_id": file_id,
        "filename": filename,
        "owner": owner,
    })


def send_access_denied_event(file_id: str, user_email: str, reason: str) -> bool:
    """Queue an access-denied event for security auditing."""
    return send_event("ACCESS_DENIED", {
        "file_id": file_id,
        "user": user_email,
        "reason": reason,
    })


def send_file_deleted_event(file_id: str, filename: str, deleted_by: str) -> bool:
    """Queue a file-deleted event."""
    return send_event("FILE_DELETED", {
        "file_id": file_id,
        "filename": filename,
        "deleted_by": deleted_by,
    })


def receive_events(max_messages: int = 10) -> list[dict]:
    """Receive and delete messages from the SQS queue (for monitoring UI)."""
    settings = get_settings()
    if not settings.sqs_queue_url:
        return []

    try:
        sqs = _get_client()
        response = sqs.receive_message(
            QueueUrl=settings.sqs_queue_url,
            MaxNumberOfMessages=min(max_messages, 10),
            WaitTimeSeconds=1,
        )
        messages = response.get("Messages", [])
        result = []
        for msg in messages:
            try:
                body = json.loads(msg["Body"])
                result.append(body)
                # Delete after reading
                sqs.delete_message(
                    QueueUrl=settings.sqs_queue_url,
                    ReceiptHandle=msg["ReceiptHandle"],
                )
            except (json.JSONDecodeError, KeyError):
                pass
        return result
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Failed to receive SQS messages: %s", exc)
        return []
