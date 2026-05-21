import json
import logging
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)


def publish_sns_alert(message: str, triggered_by: str = "system") -> bool:
    """Publish a security alert to the ZeroTrust SNS topic."""
    settings = get_settings()
    if not settings.sns_topic_arn:
        logger.warning("SNS_TOPIC_ARN not configured; skipping alert.")
        return False

    client_kwargs = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }
    if settings.aws_session_token:
        client_kwargs["aws_session_token"] = settings.aws_session_token

    try:
        sns = boto3.client("sns", **client_kwargs)
        sns.publish(
            TopicArn=settings.sns_topic_arn,
            Subject="ZeroTrust Security Alert",
            Message=json.dumps({
                "alert_type": "suspicious-access",
                "message": message,
                "triggered_by": triggered_by,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        )
        logger.info("Published SNS alert: %s", message[:80])
        return True
    except (ClientError, BotoCoreError) as exc:
        logger.exception("Failed to publish SNS alert")
        return False
