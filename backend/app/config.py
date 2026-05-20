import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv(usecwd=True))


@dataclass(frozen=True)
class Settings:
    aws_region: str
    s3_bucket_name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings(
        aws_region=os.getenv("AWS_REGION", "ap-south-1"),
        s3_bucket_name=os.getenv("S3_BUCKET_NAME", ""),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    )
