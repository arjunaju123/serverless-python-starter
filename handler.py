import json
import logging
import os
import sys
import traceback
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Setup structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Override default Lambda logging format for structured logging
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "correlation_id": "%(correlation_id)s"}'
)
handler.setFormatter(formatter)
logger.handlers = [handler]

# Global clients (for cold start optimization)
try:
    dynamodb_client = boto3.client('dynamodb')
except (BotoCoreError, ClientError) as e:
    logger.error('{"error": "Failed to initialize boto3 client", "details": "%s"}', str(e), extra={"correlation_id": "init"})
    dynamodb_client = None

def get_correlation_id(event: Dict[str, Any]) -> str:
    """Extract or generate correlation ID from event headers."""
    correlation_id = None
    try:
        correlation_id = (
            event.get("headers", {}).get("X-Correlation-Id") or
            event.get("headers", {}).get("x-correlation-id")
        )
    except Exception:
        pass
    if not correlation_id:
        correlation_id = os.urandom(8).hex()
    return correlation_id

def is_valid_event(event: Dict[str, Any]) -> bool:
    """Validate incoming event structure."""
    if not isinstance(event, dict):
        return False
    # Additional event schema validation can be added here
    return True

def send_cold_start_metric(metric_name: str, correlation_id: str) -> None:
    """Emit a custom metric (placeholder for integration with CloudWatch or X-Ray)."""
    logger.info(
        f'Emitting metric: {metric_name}',
        extra={"correlation_id": correlation_id}
    )

def hello(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    logger.info(
        "Function invoked with event",
        extra={"correlation_id": correlation_id}
    )

    # Emit custom cold start metric on first invocation
    if context and getattr(context, 'invoked_function_arn', None):
        send_cold_start_metric("ColdStart", correlation_id)

    try:
        # Input Validation
        if not is_valid_event(event):
            logger.warning("Malformed event received", extra={"correlation_id": correlation_id})
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Bad request"}),
                "headers": {
                    "Content-Type": "application/json",
                    "X-Correlation-Id": correlation_id
                }
            }

        # Example AWS SDK interaction (secure resource handling pattern)
        if dynamodb_client is not None:
            try:
                # Example: List DynamoDB tables (no-op, just as a pattern)
                response = dynamodb_client.list_tables(Limit=1)
                logger.info(
                    f'DynamoDB tables listed: {response.get("TableNames")}',
                    extra={"correlation_id": correlation_id}
                )
            except (BotoCoreError, ClientError) as sdk_error:
                logger.error(
                    f"AWS SDK error: {str(sdk_error)}",
                    extra={"correlation_id": correlation_id}
                )

        body = {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "correlation_id": correlation_id
        }

        logger.info("Function execution succeeded", extra={"correlation_id": correlation_id})

        return {
            "statusCode": 200,
            "body": json.dumps(body),
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id
            }
        }

    except Exception as exc:
        logger.error(
            f"Unhandled exception: {str(exc)} | Traceback: {traceback.format_exc()}",
            extra={"correlation_id": correlation_id}
        )
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "correlation_id": correlation_id}),
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id
            }
        }