import re
from typing import BinaryIO
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from app.config import Settings, get_settings


class S3ConfigurationError(Exception):
    pass


class S3UploadError(Exception):
    pass


def upload_file_to_s3(
    file_obj: BinaryIO,
    original_filename: str,
    content_type: str | None = None,
    settings: Settings | None = None,
) -> dict[str, str]:
    settings = settings or get_settings()
    _validate_s3_settings(settings)

    file_id = str(uuid4())
    safe_filename = _safe_filename(original_filename)
    object_key = f"uploads/{file_id}-{safe_filename}"

    client_kwargs = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }

    if settings.aws_session_token:
        client_kwargs["aws_session_token"] = settings.aws_session_token

    s3_client = boto3.client("s3", **client_kwargs)
    extra_args = {"ContentType": content_type} if content_type else None

    try:
        file_obj.seek(0)
        if extra_args:
            s3_client.upload_fileobj(file_obj, settings.s3_bucket_name, object_key, ExtraArgs=extra_args)
        else:
            s3_client.upload_fileobj(file_obj, settings.s3_bucket_name, object_key)
    except (NoCredentialsError, PartialCredentialsError) as exc:
        raise S3ConfigurationError("AWS credentials are missing or incomplete.") from exc
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")
        if error_code in {"NoSuchBucket", "InvalidBucketName"}:
            raise S3ConfigurationError("S3 bucket is missing or invalid.") from exc
        raise S3UploadError("Failed to upload file to S3.") from exc

    return {
        "file_id": file_id,
        "filename": original_filename,
        "s3_key": object_key,
    }


def _validate_s3_settings(settings: Settings) -> None:
    missing = [
        name
        for name, value in {
            "S3_BUCKET_NAME": settings.s3_bucket_name,
            "AWS_ACCESS_KEY_ID": settings.aws_access_key_id,
            "AWS_SECRET_ACCESS_KEY": settings.aws_secret_access_key,
        }.items()
        if not value
    ]

    if missing:
        raise S3ConfigurationError(f"Missing required AWS environment variables: {', '.join(missing)}.")


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", filename.strip())
    return cleaned.strip(".-") or "uploaded-file"
