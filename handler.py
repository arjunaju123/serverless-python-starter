import json
import logging
import os
import uuid
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_correlation_id(event: Dict[str, Any]) -> str:
    headers = event.get("headers", {})
    corr_id = headers.get("X-Correlation-Id") or str(uuid.uuid4())
    return corr_id


def validate_event(event: Dict[str, Any]) -> None:
    if not isinstance(event, dict):
        raise ValueError("Event payload is not a dictionary")
    # Add further validation as needed


def record_metric(metric_name: str, value: int, correlation_id: str) -> None:
    # Placeholder for custom metrics/CloudWatch (could use Embedded Metrics Format)
    logger.info(
        f"METRIC::{metric_name} VALUE::{value} CORRELATION_ID::{correlation_id}"
    )


def trace_execution(correlation_id: str) -> None:
    # Placeholder for X-Ray/tracing integration
    logger.info(f"TRACE::START CORRELATION_ID::{correlation_id}")


def hello(
    event: Dict[str, Any],
    context: Any
) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    logger.info(f"Function start - correlation_id: {correlation_id}")

    trace_execution(correlation_id)
    record_metric("function_invocation", 1, correlation_id)

    try:
        validate_event(event)

        message = (
            f"Go Serverless v1.0! Your function executed successfully! "
            f"RequestId: {getattr(context, 'aws_request_id', 'N/A')}, CorrelationId: {correlation_id}"
        )

        body = {
            "message": message,
            "correlation_id": correlation_id,
        }

        # Example boto3 usage: get the AWS region
        region = os.environ.get("AWS_REGION", "us-east-1")
        boto3_session = boto3.Session(region_name=region)
        sts_client = boto3_session.client("sts")
        try:
            account_id = sts_client.get_caller_identity()["Account"]
            body["account_id"] = account_id
        except (BotoCoreError, ClientError) as e:
            logger.error(f"boto3 error - correlation_id: {correlation_id} - {e}")
            body["account_id"] = "Unknown"

        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id,
            },
            "body": json.dumps(body),
        }
        logger.info(
            f"Function success - correlation_id: {correlation_id} - response: {json.dumps(body)}"
        )
        return response

    except ValueError as ve:
        logger.warning(f"Input validation failed - correlation_id: {correlation_id} - {ve}")
        record_metric("validation_error", 1, correlation_id)
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id,
            },
            "body": json.dumps({
                "error": "Bad Request",
                "message": str(ve),
                "correlation_id": correlation_id,
            }),
        }

    except Exception as exc:
        logger.error(f"Unhandled exception - correlation_id: {correlation_id} - {exc}", exc_info=True)
        record_metric("unhandled_exception", 1, correlation_id)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id,
            },
            "body": json.dumps({
                "error": "Internal Server Error",
                "message": "An unexpected error occurred.",
                "correlation_id": correlation_id,
            }),
        }