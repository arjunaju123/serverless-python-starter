import json
import logging
import uuid
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Configure structured logger at module load time (cold start optimization)
logger = logging.getLogger("lambda_logger")
logger.setLevel(logging.INFO)

def get_correlation_id(event: Dict[str, Any]) -> str:
    headers = event.get("headers", {}) or {}
    correlation_id = headers.get("X-Correlation-Id") or str(uuid.uuid4())
    return correlation_id

def validate_event(event: Dict[str, Any]) -> None:
    # Basic input validation
    # Extend per requirements; example: check HTTP method, path, payload size
    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary.")
    if "httpMethod" in event and event["httpMethod"] not in {"GET", "POST"}:
        raise ValueError(f"Unsupported HTTP method: {event['httpMethod']}")

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    logger.info(
        f"Lambda invocation started",
        extra={
            "correlation_id": correlation_id,
            "aws_request_id": getattr(context, "aws_request_id", None),
            "event_source": event.get("source")
        }
    )
    # Tracing, e.g., with AWS X-Ray
    if hasattr(context, "trace_id"):
        logger.info(
            f"Trace ID found",
            extra={"trace_id": context.trace_id, "correlation_id": correlation_id}
        )

    try:
        validate_event(event)

        # Example AWS SDK usage (cold start optimization: client reuse)
        s3 = boto3.client("s3")
        try:
            # Dry-run: List buckets (for illustration)
            response = s3.list_buckets()
            bucket_count = len(response.get("Buckets", []))
        except (ClientError, BotoCoreError) as aws_err:
            logger.error(
                f"AWS error occurred",
                extra={"error": str(aws_err), "correlation_id": correlation_id}
            )
            bucket_count = None

        body = {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "bucket_count": bucket_count
        }

        logger.info(
            f"Lambda executed successfully",
            extra={"correlation_id": correlation_id, "bucket_count": bucket_count}
        )

        # Example metrics (log-based, for CloudWatch extraction)
        logger.info(
            "METRIC|lambda_success|1",
            extra={"correlation_id": correlation_id}
        )

        return {
            "statusCode": 200,
            "body": json.dumps(body),
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id
            }
        }

    except ValueError as ve:
        logger.warning(
            f"Input validation failed",
            extra={"error": str(ve), "correlation_id": correlation_id}
        )
        logger.info(
            "METRIC|lambda_input_validation_error|1",
            extra={"correlation_id": correlation_id}
        )
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(ve)}),
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id
            }
        }

    except Exception as e:
        logger.exception(
            f"Unhandled exception in Lambda",
            extra={"correlation_id": correlation_id}
        )
        logger.info(
            "METRIC|lambda_unhandled_exception|1",
            extra={"correlation_id": correlation_id}
        )
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id
            }
        }