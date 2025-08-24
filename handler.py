import json
import logging
import os
import uuid
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Performance: Initialize clients outside handler for reuse
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE', 'default-table')
table = dynamodb.Table(table_name)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def sanitize_input(event: Dict[str, Any]) -> Dict[str, Any]:
    # Example: Validate event is a dictionary and sanitize keys
    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary.")
    sanitized = {}
    for key, value in event.items():
        # Strip dangerous characters from keys; shallow check for values
        sanitized_key = str(key).replace("$", "_").replace("<", "_").replace(">", "_")
        sanitized[sanitized_key] = value
    return sanitized

def record_metric(metric_name: str, value: int = 1, correlation_id: str = "") -> None:
    # Placeholder for metrics integration (e.g., AWS CloudWatch)
    logger.info(f"Metric recorded: {metric_name}={value} (correlation_id={correlation_id})")

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = (
        event.get('headers', {}).get('X-Correlation-Id')
        if isinstance(event.get('headers'), dict)
        else None
    ) or str(uuid.uuid4())

    logger.info(f"Received event: {json.dumps(event)} | correlation_id={correlation_id}")

    try:
        validated_event = sanitize_input(event)
        # Example: use boto3 (operation selected for demonstration)
        response = {}
        try:
            response = table.get_item(Key={'id': 'healthcheck'})
        except (ClientError, BotoCoreError) as db_err:
            logger.error(
                f"DynamoDB error: {db_err}",
                extra={'correlation_id': correlation_id}
            )
            record_metric("dynamodb_error", 1, correlation_id)
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "message": "Internal Server Error. DynamoDB operation failed.",
                    "correlation_id": correlation_id
                })
            }

        record_metric("lambda_invocation_success", 1, correlation_id)

        body = {
            "message": (
                "Go Serverless v1.0! Your function executed successfully!"
            ),
            "correlation_id": correlation_id,
            "dynamo_item": response.get('Item', {})
        }

        logger.info(f"Response body: {json.dumps(body)} | correlation_id={correlation_id}")
        return {
            "statusCode": 200,
            "body": json.dumps(body)
        }

    except ValueError as err:
        logger.warning(
            f"Input validation error: {err}",
            extra={'correlation_id': correlation_id}
        )
        record_metric("input_validation_error", 1, correlation_id)
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": f"Bad Request: {err}",
                "correlation_id": correlation_id
            })
        }

    except Exception as exc:
        logger.error(
            f"Unhandled error: {exc}",
            exc_info=True,
            extra={'correlation_id': correlation_id}
        )
        record_metric("lambda_invocation_error", 1, correlation_id)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal Server Error.",
                "correlation_id": correlation_id
            })
        }