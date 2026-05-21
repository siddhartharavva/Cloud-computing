"""AWS Secrets Manager integration — retrieve application secrets securely."""

import json
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)

_cached_secrets: dict | None = None


def get_secret(secret_id: str | None = None) -> dict:
    """
    Retrieve secrets from AWS Secrets Manager.

    Returns a dict of key-value pairs stored in the secret.
    Falls back to an empty dict if Secrets Manager is unavailable.
    """
    global _cached_secrets
    if _cached_secrets is not None:
        return _cached_secrets

    settings = get_settings()
    secret_id = secret_id or settings.secrets_manager_secret_id
    if not secret_id:
        logger.debug("SECRETS_MANAGER_SECRET_ID not configured; skipping.")
        return {}

    kwargs = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }
    if settings.aws_session_token:
        kwargs["aws_session_token"] = settings.aws_session_token

    try:
        client = boto3.client("secretsmanager", **kwargs)
        response = client.get_secret_value(SecretId=secret_id)
        secret_string = response.get("SecretString", "{}")
        _cached_secrets = json.loads(secret_string)
        logger.info("Successfully loaded secrets from Secrets Manager: %s", secret_id)
        return _cached_secrets
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Failed to load secrets from Secrets Manager: %s", exc)
        return {}


def list_secrets() -> list[dict]:
    """List all secret names in the account (metadata only, no values)."""
    settings = get_settings()
    kwargs = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }
    if settings.aws_session_token:
        kwargs["aws_session_token"] = settings.aws_session_token

    try:
        client = boto3.client("secretsmanager", **kwargs)
        response = client.list_secrets(MaxResults=20)
        return [
            {
                "name": s.get("Name", ""),
                "description": s.get("Description", ""),
                "last_changed": str(s.get("LastChangedDate", "")),
            }
            for s in response.get("SecretList", [])
        ]
    except (ClientError, BotoCoreError) as exc:
        logger.warning("Failed to list secrets: %s", exc)
        return []
