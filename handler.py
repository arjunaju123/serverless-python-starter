import os
import json
import logging
import uuid
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Configure logging at module level for cold start optimization
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_correlation_id(event: Dict[str, Any]) -> str:
    headers = event.get("headers", {}) or {}
    corr_id = (
        headers.get("X-Correlation-Id")
        or headers.get("x-correlation-id")
        or str(uuid.uuid4())
    )
    return corr_id

def log_with_context(level: str, message: str, correlation_id: str, **kwargs):
    log_data = {"correlation_id": correlation_id, **kwargs}
    getattr(logger, level)(f"{message} | context: {json.dumps(log_data)}")

def validate_event(event: Dict[str, Any]) -> Dict[str, Any]:
    # Accept only GET requests
    if event.get("httpMethod") not in ("GET", None):
        raise ValueError("Invalid HTTP method")

    # Optional: Validate query params/body as needed
    return event

def record_metric(metric_name: str, value: int = 1, correlation_id: str = ""):
    # This is a demonstration stub. In production, send custom metrics to CloudWatch.
    log_with_context("info", f"Metric: {metric_name}={value}", correlation_id)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    log_with_context("info", "Handler invoked", correlation_id, event_summary=str(event)[:256])

    # Optimized: boto3 clients at function scope (for cold starts)
    ssm_client = boto3.client("ssm")
    # Example: Fetch a param (demonstration, not affecting response)
    try:
        # We can safely ignore if this fails for demo; adjust for real use
        _ = ssm_client.get_parameter(Name="dummy-param")
    except (BotoCoreError, ClientError) as e:
        log_with_context("warning", f"SSM fetch error: {str(e)}", correlation_id)

    try:
        # Input validation/sanitization
        validate_event(event)

        body = {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "correlation_id": correlation_id,
        }

        record_metric("Success", 1, correlation_id)
        log_with_context("info", "Function execution successful", correlation_id, response=body)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "X-Correlation-Id": correlation_id},
            "body": json.dumps(body)
        }

    except ValueError as ve:
        record_metric("ValidationError", 1, correlation_id)
        log_with_context("error", f"Validation error: {str(ve)}", correlation_id)
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "X-Correlation-Id": correlation_id},
            "body": json.dumps({"error": "Bad Request", "message": str(ve), "correlation_id": correlation_id}),
        }
    except Exception as ex:
        record_metric("UnhandledException", 1, correlation_id)
        log_with_context("error", f"Unhandled exception: {str(ex)}", correlation_id)
        # In production, never return full exception details; keep responses generic
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "X-Correlation-Id": correlation_id},
            "body": json.dumps({"error": "Internal Server Error", "correlation_id": correlation_id}),
        }