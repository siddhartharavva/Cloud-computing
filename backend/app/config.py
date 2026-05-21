import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv(usecwd=True))


@dataclass(frozen=True)
class Settings:
    # AWS Core
    aws_region: str
    s3_bucket_name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: str | None = None

    # DynamoDB
    dynamodb_table_name: str = ""

    # KMS
    kms_key_id: str = ""

    # Cognito
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_region: str = ""

    # SNS
    sns_topic_arn: str = ""

    # SQS
    sqs_queue_url: str = ""

    # CloudWatch
    cloudwatch_log_group: str = ""

    # Secrets Manager
    secrets_manager_secret_id: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings(
        aws_region=os.getenv("AWS_REGION", "ap-south-1"),
        s3_bucket_name=os.getenv("S3_BUCKET_NAME", ""),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        dynamodb_table_name=os.getenv("DYNAMODB_TABLE_NAME", "ZeroTrustFiles"),
        kms_key_id=os.getenv("KMS_KEY_ID", "alias/zt-file-exchange"),
        cognito_user_pool_id=os.getenv("COGNITO_USER_POOL_ID", ""),
        cognito_app_client_id=os.getenv("COGNITO_APP_CLIENT_ID", ""),
        cognito_region=os.getenv("COGNITO_REGION", "ap-south-1"),
        sns_topic_arn=os.getenv("SNS_TOPIC_ARN", ""),
        sqs_queue_url=os.getenv("SQS_QUEUE_URL", ""),
        cloudwatch_log_group=os.getenv("CLOUDWATCH_LOG_GROUP", "/zerotrust/backend"),
        secrets_manager_secret_id=os.getenv("SECRETS_MANAGER_SECRET_ID", ""),
    )
