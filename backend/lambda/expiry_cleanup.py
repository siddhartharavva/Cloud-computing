"""AWS Lambda handler for scheduled file expiry cleanup.

Triggered by EventBridge rule on a schedule (e.g. every hour).
Scans DynamoDB for active files past their expiry_at timestamp,
deletes them from S3, and marks them expired in DynamoDB.

Environment variables:
    DYNAMODB_TABLE_NAME: DynamoDB table name (default: ZeroTrustFiles)
    S3_BUCKET_NAME: S3 bucket name
    AWS_REGION: AWS region
"""

import logging
import os
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    table_name = os.environ.get("DYNAMODB_TABLE_NAME", "ZeroTrustFiles")
    bucket_name = os.environ.get("S3_BUCKET_NAME", "")
    region = os.environ.get("AWS_REGION", "ap-south-1")

    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)
    s3 = boto3.client("s3", region_name=region)
    sns = boto3.client("sns", region_name=region)

    now = datetime.now(timezone.utc).isoformat()

    logger.info("Starting expiry scan at %s", now)

    response = table.scan(
        FilterExpression="#s = :active AND expiry_at < :now",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":active": "Active", ":now": now},
    )

    items = response.get("Items", [])
    logger.info("Found %d expired files", len(items))

    cleaned = 0
    for item in items:
        file_id = item.get("file_id", "unknown")
        s3_key = item.get("s3_key", "")
        try:
            if s3_key and bucket_name:
                s3.delete_object(Bucket=bucket_name, Key=s3_key)
                logger.info("Deleted S3 object: %s", s3_key)
            table.update_item(
                Key={"file_id": file_id},
                UpdateExpression="SET #s = :expired",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":expired": "Expired"},
            )
            cleaned += 1
            logger.info("Marked file %s as expired", file_id)
        except Exception as exc:
            logger.error("Failed to clean up file %s: %s", file_id, exc)

    # Send SNS notification about cleanup
    sns_topic_arn = os.environ.get("SNS_TOPIC_ARN", "")
    if sns_topic_arn and cleaned > 0:
        try:
            sns.publish(
                TopicArn=sns_topic_arn,
                Subject="ZeroTrust Lifecycle - Files Expired",
                Message=f"EventBridge scheduled scan expired {cleaned} file(s) at {now}.",
            )
        except Exception as exc:
            logger.warning("SNS notification failed: %s", exc)

    result = {"expired_count": cleaned, "scanned_at": now}
    logger.info("Expiry scan complete: %s", result)
    return result
