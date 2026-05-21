import json
import logging
import time
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)

_log_stream_name: str | None = None
_sequence_token: str | None = None


def _get_clients():
    settings = get_settings()
    kwargs = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }
    if settings.aws_session_token:
        kwargs["aws_session_token"] = settings.aws_session_token
    logs_client = boto3.client("logs", **kwargs)
    cw_client = boto3.client("cloudwatch", **kwargs)
    return logs_client, cw_client


def _ensure_log_stream():
    global _log_stream_name
    settings = get_settings()
    if not settings.cloudwatch_log_group:
        return None
    if _log_stream_name:
        return _log_stream_name
    logs, _ = _get_clients()
    _log_stream_name = f"backend-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    try:
        logs.create_log_group(logGroupName=settings.cloudwatch_log_group)
    except logs.exceptions.ResourceAlreadyExistsException:
        pass
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Could not create log group: %s", exc)
    try:
        logs.create_log_stream(
            logGroupName=settings.cloudwatch_log_group,
            logStreamName=_log_stream_name,
        )
    except logs.exceptions.ResourceAlreadyExistsException:
        pass
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Could not create log stream: %s", exc)
    return _log_stream_name


def put_log_event(service: str, event_type: str, message: str, severity: str = "info") -> None:
    """Write a structured log event to CloudWatch Logs."""
    settings = get_settings()
    if not settings.cloudwatch_log_group:
        return
    stream = _ensure_log_stream()
    if not stream:
        return
    logs_client, _ = _get_clients()
    event = {
        "service": service,
        "type": event_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        logs_client.put_log_events(
            logGroupName=settings.cloudwatch_log_group,
            logStreamName=stream,
            logEvents=[{"timestamp": int(time.time() * 1000), "message": json.dumps(event)}],
        )
    except (ClientError, BotoCoreError) as exc:
        logger.warning("CloudWatch put_log_events failed: %s", exc)


def put_metric(name: str, value: float = 1.0, unit: str = "Count") -> None:
    """Push a custom metric to CloudWatch."""
    settings = get_settings()
    if not settings.cloudwatch_log_group:
        return
    _, cw = _get_clients()
    try:
        cw.put_metric_data(
            Namespace="ZeroTrust",
            MetricData=[{"MetricName": name, "Value": value, "Unit": unit}],
        )
    except (ClientError, BotoCoreError) as exc:
        logger.warning("CloudWatch put_metric_data failed: %s", exc)


def get_recent_logs(limit: int = 20) -> list[dict]:
    """Read recent log events from CloudWatch for the /logs endpoint."""
    settings = get_settings()
    if not settings.cloudwatch_log_group:
        return _fallback_logs()
    logs_client, _ = _get_clients()
    try:
        streams = logs_client.describe_log_streams(
            logGroupName=settings.cloudwatch_log_group,
            orderBy="LastEventTime",
            descending=True,
            limit=3,
        )
        result = []
        for stream in streams.get("logStreams", []):
            events = logs_client.get_log_events(
                logGroupName=settings.cloudwatch_log_group,
                logStreamName=stream["logStreamName"],
                limit=limit,
                startFromHead=False,
            )
            for ev in events.get("events", []):
                try:
                    parsed = json.loads(ev["message"])
                    parsed["id"] = f"log-{ev['timestamp']}"
                    parsed["time"] = parsed.get("timestamp", "")
                    result.append(parsed)
                except (json.JSONDecodeError, KeyError):
                    result.append({
                        "id": f"log-{ev['timestamp']}",
                        "service": "Backend",
                        "type": "Raw log",
                        "message": ev["message"],
                        "severity": "info",
                        "time": datetime.fromtimestamp(
                            ev["timestamp"] / 1000, tz=timezone.utc
                        ).isoformat(),
                    })
        result.sort(key=lambda x: x.get("time", ""), reverse=True)
        return result[:limit]
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Failed to read CloudWatch logs: %s", exc)
        return _fallback_logs()


def _fallback_logs() -> list[dict]:
    """Return minimal placeholder logs when CloudWatch is unavailable."""
    return [
        {
            "id": "log-fallback-1",
            "service": "System",
            "type": "Status",
            "message": "CloudWatch log group not configured. Showing local placeholder.",
            "severity": "info",
            "time": datetime.now(timezone.utc).isoformat(),
        }
    ]
