import json
import logging
import os
import uuid
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Optimize logging for Lambda cold start
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Ensure boto3 client is reused for Lambda warm starts
# For demonstration, use sts client (could be replaced by any required AWS service client)
_sts_client = None

def get_sts_client():
    global _sts_client
    if _sts_client is None:
        _sts_client = boto3.client("sts")
    return _sts_client

def extract_correlation_id(event: Dict[str, Any]) -> str:
    headers = event.get("headers", {}) or {}
    # Try several common locations for correlation ID
    correlation_id = (
        headers.get("x-correlation-id") or
        headers.get("X-Correlation-ID") or
        event.get("requestContext", {}).get("requestId") or
        str(uuid.uuid4())
    )
    return correlation_id

def validate_input(event: Dict[str, Any]) -> None:
    # Example basic input validation
    if not isinstance(event, dict):
        raise ValueError("Event payload must be a dictionary.")
    # Add other necessary validations here (e.g., validation for query params, etc.)

def log_metric(name: str, value: float, correlation_id: str = "") -> None:
    # Placeholder for observability/metrics integration
    logger.info(f"METRIC - {name}: {value} correlation_id={correlation_id}")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = extract_correlation_id(event)
    logger.info(
        f"Handler invoked for request: correlation_id={correlation_id}",
        extra={"correlation_id": correlation_id, "event": event}
    )

    try:
        validate_input(event)
        
        # Observability example: increment an invocation counter
        log_metric("lambda_invocation_count", 1, correlation_id)

        # Example AWS SDK usage (sts GetCallerIdentity)
        # This demonstrates boto3 client usage and error handling
        try:
            sts_client = get_sts_client()
            sts_response = sts_client.get_caller_identity()
        except (BotoCoreError, ClientError) as boto_err:
            logger.error(
                f"Boto3 error occurred: {boto_err}",
                extra={"correlation_id": correlation_id}
            )
            return {
                "statusCode": 502,
                "body": json.dumps({
                    "message": "Error accessing AWS service.",
                    "correlation_id": correlation_id
                })
            }

        body = {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "account": sts_response.get("Account"),
            "correlation_id": correlation_id
        }

        logger.info(
            f"Function executed successfully. correlation_id={correlation_id}",
            extra={"correlation_id": correlation_id, "response": body}
        )

        return {
            "statusCode": 200,
            "body": json.dumps(body)
        }

    except ValueError as ve:
        logger.warning(
            f"Input validation error: {ve}",
            extra={"correlation_id": correlation_id}
        )
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": f"Invalid input: {ve}",
                "correlation_id": correlation_id
            })
        }
    except Exception as ex:
        logger.error(
            f"Unhandled exception: {ex}",
            exc_info=True,
            extra={"correlation_id": correlation_id}
        )
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal server error.",
                "correlation_id": correlation_id
            })
        }