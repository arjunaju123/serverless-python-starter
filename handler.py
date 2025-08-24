import json
import logging
import os
import traceback
import uuid
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Set up structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cold start optimizations: initialize resources outside handler
session = boto3.Session()
# Example AWS resource, e.g., s3 = session.client('s3')


def get_correlation_id(event: Dict[str, Any]) -> str:
    """Retrieve or generate correlation ID for the invocation."""
    headers = event.get("headers", {}) or {}
    corr_id = headers.get("X-Correlation-Id") or headers.get("x-correlation-id")
    if not corr_id:
        corr_id = str(uuid.uuid4())
    return corr_id


def validate_event(event: Dict[str, Any]) -> None:
    """Input validation and sanitization."""
    if not isinstance(event, dict):
        raise ValueError("Invalid event: Must be a dictionary.")
    # Example: Restricted message size
    body = event.get("body")
    if body and len(str(body)) > 2048:
        raise ValueError("Event body too large.")


def hello(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    try:
        validate_event(event)

        logger.info(
            "Lambda invocation started",
            extra={
                "correlation_id": correlation_id,
                "function": context.function_name if context else "unknown",
                "aws_request_id": getattr(context, 'aws_request_id', None)
            }
        )

        # Example of using boto3 with modern patterns
        # Example AWS call - replace with actual call if needed
        # response = s3.list_buckets()
        # buckets = [b['Name'] for b in response.get('Buckets', [])]

        message = "Go Serverless v1.0! Your function executed successfully!"
        logger.info(
            "Lambda invocation succeeded",
            extra={
                "correlation_id": correlation_id,
                "message": message
                # "buckets": buckets
            }
        )

        response_body = {
            "message": message,
            "correlation_id": correlation_id,
            # "buckets": buckets
        }

        # Observability: Emit a custom metric (example, replace as needed)
        if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            try:
                client = session.client("cloudwatch")
                client.put_metric_data(
                    Namespace="Serverless/HelloFunc",
                    MetricData=[
                        {
                            "MetricName": "Invocations",
                            "Dimensions": [{"Name": "FunctionName", "Value": context.function_name if context else "unknown"}],
                            "Value": 1,
                            "Unit": "Count"
                        }
                    ]
                )
            except (BotoCoreError, ClientError) as metric_exc:
                logger.error(
                    "Metric emission failed",
                    extra={
                        "correlation_id": correlation_id,
                        "error": str(metric_exc)
                    }
                )

        return {
            "statusCode": 200,
            "body": json.dumps(response_body),
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id
            }
        }

    except Exception as exc:
        logger.error(
            "Lambda invocation failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(exc),
                "traceback": traceback.format_exc()
            }
        )

        body = {
            "message": "An internal error occurred.",
            "correlation_id": correlation_id
        }
        return {
            "statusCode": 500,
            "body": json.dumps(body),
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id
            }
        }