import json
import logging
import os
import uuid
from http import HTTPStatus
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Pre-create logger for cold start optimization
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Optional: Pre-instantiate boto3 resource/client here if needed in cold start
# Example: dynamodb_client = boto3.client('dynamodb')

def get_correlation_id(event: Dict[str, Any]) -> str:
    # Try to get correlation-id from event headers, else generate
    headers = event.get('headers') or {}
    cid = headers.get('x-correlation-id') or headers.get('X-Correlation-ID')
    if not cid:
        cid = str(uuid.uuid4())
    return cid

def validate_event(event: Dict[str, Any]) -> None:
    # Basic input validation (expand as needed)
    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary.")
    if 'body' in event and event['body'] is not None:
        try:
            json.loads(event['body'])
        except (ValueError, TypeError) as exc:
            raise ValueError("Event body must be valid JSON.") from exc

def send_metric(metric_name: str, value: int = 1, correlation_id: str = "") -> None:
    try:
        cloudwatch = boto3.client('cloudwatch')
        cloudwatch.put_metric_data(
            Namespace='ServerlessDemo',
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'CorrelationId', 'Value': correlation_id}
                    ]
                },
            ]
        )
    except (BotoCoreError, ClientError) as exc:
        logger.error(f"[{correlation_id}] Metric logging failed: {exc}")

def hello(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    # Start Tracing Placeholder (multi-cloud, replace with preferred solution)
    trace_id = os.environ.get("AWS_XRAY_TRACE_ID", uuid.uuid4().hex)
    logger.info(
        f"[{correlation_id}] Function invoked. TraceId={trace_id}, RequestId={getattr(context, 'aws_request_id', 'N/A')}"
    )
    metric_sent = False

    try:
        validate_event(event)
        # Main business logic
        body = {
            "message": "Go Serverless v1.0! Your function executed successfully!",
        }
        # Example AWS SDK usage (commented unless needed)
        # response = dynamodb_client.list_tables()
        # body['dynamodb_tables'] = response.get('TableNames', [])
        response = {
            "statusCode": HTTPStatus.OK,
            "body": json.dumps(body),
            "headers": {
                "Content-Type": "application/json",
                "x-correlation-id": correlation_id,
            }
        }
        send_metric("HelloSuccess", 1, correlation_id)
        metric_sent = True
        logger.info(f"[{correlation_id}] Success response returned.")
        return response

    except (ValueError, TypeError) as exc:
        logger.error(f"[{correlation_id}] Input validation error: {exc}")
        send_metric("HelloValidationError", 1, correlation_id)
        return {
            "statusCode": HTTPStatus.BAD_REQUEST,
            "body": json.dumps({"error": str(exc)}),
            "headers": {
                "Content-Type": "application/json",
                "x-correlation-id": correlation_id,
            }
        }

    except (BotoCoreError, ClientError) as exc:
        logger.error(f"[{correlation_id}] AWS SDK error: {exc}")
        send_metric("HelloAWSError", 1, correlation_id)
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": json.dumps({"error": "AWS service error"}),
            "headers": {
                "Content-Type": "application/json",
                "x-correlation-id": correlation_id,
            }
        }

    except Exception as exc:
        logger.exception(f"[{correlation_id}] Unexpected error: {exc}")
        if not metric_sent:
            send_metric("HelloUnhandledError", 1, correlation_id)
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": {
                "Content-Type": "application/json",
                "x-correlation-id": correlation_id,
            }
        }