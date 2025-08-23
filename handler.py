import json
import logging
import os
import uuid
import time
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    # Initialize AWS resources outside the handler for cold start optimization
    dynamodb = boto3.resource("dynamodb")
    metrics_namespace = os.environ.get("METRICS_NAMESPACE", "ServerlessHelloFunction")
except (BotoCoreError, ClientError) as e:
    logger.error(f"Failed to initialize AWS resources: {e}")
    dynamodb = None  # Fallback for resource errors

def get_correlation_id(event: Dict[str, Any]) -> str:
    # Use an incoming correlation ID if present, otherwise generate a new one
    headers = event.get("headers", {})
    correlation_id = (
        headers.get("x-correlation-id")
        or event.get("requestContext", {}).get("requestId")
        or str(uuid.uuid4())
    )
    return correlation_id

def sanitize_input(event: Dict[str, Any]) -> Dict[str, Any]:
    # Basic input sanitization: Ensure event isn't too large or malformed
    try:
        if "body" in event and event["body"]:
            body = event["body"]
            if isinstance(body, str):
                body = json.loads(body)
            if not isinstance(body, dict):
                raise ValueError("Invalid body structure.")
            if len(json.dumps(body)) > 1024 * 10:  # limit body size to 10KB
                raise ValueError("Payload too large.")
            event["body"] = body
        return event
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Invalid input payload: {e}")

def put_metric(metric_name: str, value: float = 1.0, unit: str = "Count") -> None:
    try:
        cloudwatch = boto3.client("cloudwatch")
        cloudwatch.put_metric_data(
            Namespace=metrics_namespace,
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Timestamp": int(time.time()),
                    "Value": value,
                    "Unit": unit,
                }
            ],
        )
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to put CloudWatch metric {metric_name}: {e}")

def hello(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    start_time = time.time()
    correlation_id = get_correlation_id(event)
    logger.info(
        f"Received event for Lambda execution",
        extra={"correlation_id": correlation_id, "event": event}
    )

    try:
        # Input validation & sanitization
        event = sanitize_input(event)

        body = {
            "message": (
                "Go Serverless v1.0! Your function executed successfully!"
            ),
            "correlation_id": correlation_id,
        }

        # (Example usage of AWS SDK) - List tables as a health check
        if dynamodb:
            try:
                table_names = list(dynamodb.tables.all())
                body["dynamodb_table_count"] = len(table_names)
            except (BotoCoreError, ClientError) as aws_error:
                logger.warning(
                    f"Error while accessing DynamoDB tables: {aws_error}",
                    extra={"correlation_id": correlation_id}
                )
                body["dynamodb_table_count"] = "error"

        # Observability: Custom metric, basic tracing
        put_metric("Success")

        duration = round(time.time() - start_time, 6)
        logger.info(
            f"Function executed in {duration} seconds",
            extra={"correlation_id": correlation_id, "duration": duration}
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "x-correlation-id": correlation_id,
            },
            "body": json.dumps(body),
        }
    except ValueError as ve:
        logger.error(f"Input validation error: {ve}", extra={"correlation_id": correlation_id})
        put_metric("InputValidationError")
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "x-correlation-id": correlation_id,
            },
            "body": json.dumps({"error": str(ve), "correlation_id": correlation_id}),
        }
    except Exception as exc:
        logger.exception("Unhandled exception in Lambda handler", extra={"correlation_id": correlation_id})
        put_metric("UnhandledException")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "x-correlation-id": correlation_id,
            },
            "body": json.dumps(
                {
                    "error": "Internal server error.",
                    "correlation_id": correlation_id,
                }
            ),
        }