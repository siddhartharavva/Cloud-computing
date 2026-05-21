import logging
import re
from typing import BinaryIO
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, PartialCredentialsError

from app.config import Settings, get_settings


logger = logging.getLogger(__name__)


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

    logger.info("Preparing S3 upload")
    logger.info("S3 bucket: %s", settings.s3_bucket_name)
    logger.info("AWS region: %s", settings.aws_region)
    logger.info("Generated S3 key: %s", object_key)

    client_kwargs = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }

    if settings.aws_session_token:
        client_kwargs["aws_session_token"] = settings.aws_session_token

    try:
        s3_client = boto3.client("s3", **client_kwargs)
        logger.info("boto3 S3 client initialized")
    except (NoCredentialsError, PartialCredentialsError) as exc:
        logger.exception("AWS credentials are missing or incomplete during client initialization")
        raise S3ConfigurationError("AWS credentials are missing or incomplete.") from exc
    except BotoCoreError as exc:
        logger.exception("Failed to initialize boto3 S3 client")
        raise S3ConfigurationError(f"Failed to initialize S3 client: {exc}") from exc

    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type
    if settings.kms_key_id:
        extra_args["ServerSideEncryption"] = "aws:kms"
        extra_args["SSEKMSKeyId"] = settings.kms_key_id

    try:
        file_obj.seek(0)
        s3_client.upload_fileobj(
            file_obj,
            settings.s3_bucket_name,
            object_key,
            ExtraArgs=extra_args if extra_args else None,
        )
        logger.info("S3 upload completed: s3://%s/%s", settings.s3_bucket_name, object_key)
    except (NoCredentialsError, PartialCredentialsError) as exc:
        logger.exception("AWS credentials are missing or incomplete during upload")
        raise S3ConfigurationError("AWS credentials are missing or incomplete.") from exc
    except ClientError as exc:
        error = exc.response.get("Error", {})
        error_code = error.get("Code", "Unknown")
        error_message = error.get("Message", "No message provided by AWS.")
        headers = exc.response.get("ResponseMetadata", {}).get("HTTPHeaders", {})
        bucket_region = headers.get("x-amz-bucket-region")

        logger.exception(
            "boto3 ClientError during S3 upload. code=%s message=%s bucket_region=%s",
            error_code,
            error_message,
            bucket_region,
        )
        if error_code in {"NoSuchBucket", "InvalidBucketName"}:
            raise S3ConfigurationError(
                f"S3 bucket is missing or invalid: {settings.s3_bucket_name}."
            ) from exc
        if error_code in {"AuthorizationHeaderMalformed", "IllegalLocationConstraintException", "PermanentRedirect"}:
            region_hint = f" Bucket region appears to be {bucket_region}." if bucket_region else ""
            raise S3ConfigurationError(
                f"S3 bucket region mismatch. Configured region is {settings.aws_region}.{region_hint}"
            ) from exc
        if error_code in {"AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"}:
            raise S3ConfigurationError(f"AWS credential or permission error: {error_code}.") from exc

        raise S3UploadError(f"Failed to upload file to S3: {error_code} - {error_message}") from exc
    except BotoCoreError as exc:
        logger.exception("boto3 core error during S3 upload")
        raise S3UploadError(f"Failed to upload file to S3: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected error during S3 upload")
        raise S3UploadError(f"Unexpected S3 upload error: {exc}") from exc

    return {
        "file_id": file_id,
        "filename": original_filename,
        "s3_key": object_key,
    }


def generate_presigned_url(
    s3_key: str,
    expires_in: int = 300,
    settings: Settings | None = None,
) -> str:
    """Generate a temporary pre-signed URL for secure file download."""
    settings = settings or get_settings()
    client_kwargs = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }
    if settings.aws_session_token:
        client_kwargs["aws_session_token"] = settings.aws_session_token
    s3 = boto3.client("s3", **client_kwargs)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_name, "Key": s3_key},
        ExpiresIn=expires_in,
    )


def delete_s3_object(
    s3_key: str,
    settings: Settings | None = None,
) -> None:
    """Delete an object from S3."""
    settings = settings or get_settings()
    client_kwargs = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }
    if settings.aws_session_token:
        client_kwargs["aws_session_token"] = settings.aws_session_token
    s3 = boto3.client("s3", **client_kwargs)
    s3.delete_object(Bucket=settings.s3_bucket_name, Key=s3_key)
    logger.info("Deleted S3 object: s3://%s/%s", settings.s3_bucket_name, s3_key)


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
