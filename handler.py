import json
import logging
import os
import traceback
import uuid
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Configure logging once at module load (cold start optimization)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set up custom metrics (CloudWatch Embedded Metric Format)
def put_custom_metric(name: str, value: float, correlation_id: str) -> None:
    # For larger workloads, consider using the aws-embedded-metrics lib
    metric = {
        "_aws": {
            "Timestamp": int(__import__("time").time() * 1000),
            "CloudWatchMetrics": [
                {
                    "Namespace": "MyApp/Lambda",
                    "Dimensions": [["FunctionName", "CorrelationId"]],
                    "Metrics": [{"Name": name, "Unit": "Count"}],
                }
            ],
        },
        "FunctionName": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "UnknownFunction"),
        "CorrelationId": correlation_id,
        name: value,
    }
    logger.info(json.dumps(metric))

# Helper to extract or generate a correlation ID
def get_correlation_id(event: Dict[str, Any]) -> str:
    headers = event.get("headers", {}) or {}
    # Try several common headers; else generate one
    possible_keys = ["x-correlation-id", "X-Correlation-Id", "correlation-id", "requestId"]
    for k in possible_keys:
        value = headers.get(k)
        if value:
            return str(value)
    return str(uuid.uuid4())

# Sanitize input (add checks as needed for your endpoint)
def validate_event(event: Dict[str, Any]) -> None:
    if not isinstance(event, dict):
        raise ValueError("Event object must be a dictionary.")

def hello(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    logger.info(f"Invocation start", extra={"correlation_id": correlation_id})
    put_custom_metric("Invocations", 1, correlation_id)
    try:
        validate_event(event)

        # If you need AWS SDK, e.g., boto3 client, initialize in global scope for reuse
        # s3 = boto3.client("s3")
        # Demonstrating AWS SDK error handling
        # try:
        #     result = s3.list_buckets()
        # except (ClientError, BotoCoreError) as e:
        #     logger.error("Boto3 error", extra={"error": str(e), "correlation_id": correlation_id})
        #     raise

        body = {
            "message": "Go Serverless v1.0! Your function executed successfully!"
        }

        logger.info("Function executed successfully", extra={"correlation_id": correlation_id})
        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "x-correlation-id": correlation_id,
            },
            "body": json.dumps(body),
        }
        put_custom_metric("Successes", 1, correlation_id)
        return response

    except (ValueError, TypeError) as ve:
        error_message = f"Input validation error: {ve}"
        logger.warning(error_message, extra={"correlation_id": correlation_id})
        put_custom_metric("ValidationErrors", 1, correlation_id)
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "x-correlation-id": correlation_id,
            },
            "body": json.dumps({"error": error_message}),
        }
    except (ClientError, BotoCoreError) as aws_error:
        error_message = f"AWS SDK error: {aws_error}"
        logger.error(error_message, extra={"correlation_id": correlation_id})
        put_custom_metric("AwsSdkErrors", 1, correlation_id)
        return {
            "statusCode": 502,
            "headers": {
                "Content-Type": "application/json",
                "x-correlation-id": correlation_id,
            },
            "body": json.dumps({"error": error_message}),
        }
    except Exception as ex:
        # Unhandled error, ensure traceback is logged
        trace = traceback.format_exc()
        logger.error(f"Unhandled exception: {ex}", extra={"traceback": trace, "correlation_id": correlation_id})
        put_custom_metric("UnhandledErrors", 1, correlation_id)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "x-correlation-id": correlation_id,
            },
            "body": json.dumps({"error": "Internal server error"}),
        }