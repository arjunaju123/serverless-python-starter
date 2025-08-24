import json
import logging
import os
import traceback
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Setup structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global AWS resource initialization (cold start optimization)
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))

def _get_correlation_id(event: Dict[str, Any]) -> str:
    # Try to get correlation id from headers, fallback to context/request id
    headers = event.get("headers", {})
    correlation_id = (
        headers.get("X-Correlation-Id")
        or headers.get("x-correlation-id")
        or event.get("requestContext", {}).get("requestId")
        or ""
    )
    return correlation_id

def _validate_event(event: Dict[str, Any]) -> None:
    # Example: ensure queryStringParameters and certain keys exist
    # Expand as needed for input validation & sanitization
    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary.")
    # Add additional validation if expecting body or parameters

def hello(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = _get_correlation_id(event)
    # Observability: basic metric (extend using CloudWatch or Embedded Metrics Library)
    logger.info(
        "Lambda invoked",
        extra={
            "function_name": context.function_name if context else None,
            "correlation_id": correlation_id,
            "aws_request_id": getattr(context, "aws_request_id", None),
        },
    )

    try:
        _validate_event(event)

        # Example DynamoDB health check (optional): verify connection
        try:
            dynamodb_tables = list(dynamodb.tables.all())
            logger.debug(f"DynamoDB Tables: {[t.name for t in dynamodb_tables]}")
        except (BotoCoreError, ClientError) as db_exc:
            logger.warning(
                f"DynamoDB connection failed: {db_exc}",
                extra={"correlation_id": correlation_id},
            )

        body = {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "correlation_id": correlation_id,
        }

        response = {
            "statusCode": 200,
            "body": json.dumps(body),
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id,
            },
        }
        logger.info(
            "Lambda response",
            extra={
                "status_code": response["statusCode"],
                "correlation_id": correlation_id,
            },
        )
        return response

    except Exception as exc:
        error_msg = f"Handler error: {exc}"
        logger.error(
            error_msg,
            extra={
                "correlation_id": correlation_id,
                "trace": traceback.format_exc(),
            },
        )
        error_body = {
            "error": "Internal Server Error",
            "correlation_id": correlation_id,
            "detail": str(exc),
        }
        # Observability: log error metric/event here as needed
        return {
            "statusCode": 500,
            "body": json.dumps(error_body),
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id,
            },
        }