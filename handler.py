import json
import logging
import os
import sys
import uuid
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Cold start global initialization
logger = logging.getLogger()
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '{"timestamp":"%(asctime)s", "level":"%(levelname)s", "correlation_id":"%(correlation_id)s", "message":"%(message)s"}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def get_correlation_id(event: Dict[str, Any]) -> str:
    headers = event.get('headers') or {}
    return (
        headers.get('X-Correlation-Id')
        or event.get('requestContext', {}).get('requestId')
        or str(uuid.uuid4())
    )

def log_with_correlation(level: int, message: str, correlation_id: str) -> None:
    extra = {'correlation_id': correlation_id}
    logger.log(level, message, extra=extra)

def sanitize_message(message: str) -> str:
    if not isinstance(message, str):
        return "Invalid message type."
    # Basic sanitization; more may be needed for other data
    return message.replace("\n", " ").replace("\r", " ")

def validate_event(event: Dict[str, Any]) -> bool:
    if not isinstance(event, dict):
        return False
    return True

def record_metric(metric_name: str, value: float, correlation_id: str) -> None:
    # Placeholder for metrics; integrate with CloudWatch Embedded Metrics as needed
    log_with_correlation(logging.INFO, f"METRIC {metric_name}: {value}", correlation_id)

def trace_execution(context: Any, correlation_id: str) -> None:
    # Placeholder for integration with AWS X-Ray or other tracing tools
    log_with_correlation(logging.INFO, f"TRACE start - aws_request_id: {getattr(context, 'aws_request_id', '')}", correlation_id)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    trace_execution(context, correlation_id)
    record_metric("lambda_invocation", 1, correlation_id)

    try:
        if not validate_event(event):
            log_with_correlation(logging.ERROR, "Invalid event received", correlation_id)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Bad Request"}),
                "headers": {"X-Correlation-Id": correlation_id}
            }

        # Example boto3 usage with error handling
        try:
            # Demonstrating cold-start optimized resource
            s3_client = boto3.client('s3')
            # List buckets to illustrate AWS SDK pattern
            response = s3_client.list_buckets()
            bucket_names = [sanitize_message(b.get('Name', '')) for b in response.get('Buckets', [])]
        except (BotoCoreError, ClientError) as aws_error:
            log_with_correlation(logging.ERROR, f"AWS SDK error: {aws_error}", correlation_id)
            bucket_names = []

        body = {
            "message": sanitize_message("Go Serverless v1.0! Your function executed successfully!"),
            "buckets": bucket_names,
            "correlation_id": correlation_id
        }

        log_with_correlation(logging.INFO, "Function executed successfully", correlation_id)
        record_metric("lambda_success", 1, correlation_id)
        return {
            "statusCode": 200,
            "body": json.dumps(body),
            "headers": {"X-Correlation-Id": correlation_id}
        }
    except Exception as ex:
        log_with_correlation(logging.ERROR, f"Unhandled exception: {ex}", correlation_id)
        record_metric("lambda_error", 1, correlation_id)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal Server Error", "correlation_id": correlation_id}),
            "headers": {"X-Correlation-Id": correlation_id}
        }