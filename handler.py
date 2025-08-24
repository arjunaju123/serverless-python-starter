import json
import logging
import uuid
import os
from typing import Any, Dict
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Initialize logger at module level for cold start optimization
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Metrics/tracing placeholders (use AWS Embedded Metrics, X-Ray, or similar in production)
def record_metric(name: str, value: float, correlation_id: str) -> None:
    logger.info(f"Metric recorded: {name}={value}, correlation_id={correlation_id}")

def trace_event(name: str, details: Dict[str, Any], correlation_id: str) -> None:
    logger.info(f"Trace event: {name}, details={details}, correlation_id={correlation_id}")

# AWS SDK client initialized once per container (optimized for cold start)
session = boto3.session.Session()
lambda_client = session.client('lambda')

def validate_input(event: Dict[str, Any]) -> None:
    # Example validation – ensure event is dict and sanitize fields
    if not isinstance(event, dict):
        raise ValueError("Invalid event: not a dict")
    # Add specific field checks as needed
    # Example: check for 'requestContext' or 'headers' if required in future
    
def get_correlation_id(event: Dict[str, Any]) -> str:
    # Prefer explicit correlation ID from headers/requestContext if available
    corr_id = (
        event.get('headers', {}).get('X-Correlation-ID') or
        event.get('requestContext', {}).get('requestId') or
        str(uuid.uuid4())
    )
    return corr_id

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    logger_adapter = logging.LoggerAdapter(logger, {'correlation_id': correlation_id})
    try:
        validate_input(event)

        logger_adapter.info("Lambda execution started", extra={'event': event})
        trace_event('lambda_execution_started', {'event': event}, correlation_id)

        # Example AWS SDK usage
        try:
            # Minimal usage for demonstration; e.g., getting our Lambda's info
            response = lambda_client.get_function(FunctionName=os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'unknown'))
            logger_adapter.info("Fetched Lambda function info", extra={'data': response})
        except (BotoCoreError, ClientError) as aws_err:
            logger_adapter.warning(f"AWS SDK error: {aws_err}", extra={'error': str(aws_err)})
            response = None  # Continue gracefully

        body = {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "correlation_id": correlation_id,
            "function_info": response or "unavailable"
        }
        record_metric('successful_execution', 1, correlation_id)
        trace_event('lambda_success', body, correlation_id)

        return {
            "statusCode": 200,
            "body": json.dumps(body)
        }

    except ValueError as ve:
        logger_adapter.error(f"Input validation error: {ve}", exc_info=True)
        record_metric('validation_error', 1, correlation_id)
        trace_event('lambda_validation_error', {'error': str(ve)}, correlation_id)
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid input", "correlation_id": correlation_id})
        }
    except Exception as exc:
        logger_adapter.error(f"Unhandled exception: {exc}", exc_info=True)
        record_metric('internal_error', 1, correlation_id)
        trace_event('lambda_internal_error', {'error': str(exc)}, correlation_id)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "correlation_id": correlation_id})
        }

# For the Serverless Framework config:
# entrypoint = handler.lambda_handler