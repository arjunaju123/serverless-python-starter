import json
import logging
import uuid
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from typing import Any, Dict
import re
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    # Optimize for cold start performance: initialize clients OUTSIDE handler
    ssm_client = boto3.client('ssm')
except (BotoCoreError, ClientError) as e:
    logger.error(f"Boto3 initialization failed: {e}")
    ssm_client = None  # To handle boto3 failure gracefully

def sanitize_input(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basic input sanitization/validation tailored for API Gateway events.
    """
    # Example: allow only alphanumeric pathParameters
    path_params = event.get('pathParameters', {})
    sanitized = {}
    for k, v in path_params.items() if path_params else []:
        if v and re.match(r'^\w+$', v):
            sanitized[k] = v
        else:
            sanitized[k] = None
    event['pathParameters'] = sanitized
    return event

def record_metric(metric_name: str, value: int = 1) -> None:
    # No-op: placeholder for metrics integration (e.g., CloudWatch Embedded Metric Format)
    pass

def trace_start(correlation_id: str) -> None:
    # No-op: placeholder for distributed tracing start
    pass

def trace_end(correlation_id: str) -> None:
    # No-op: placeholder for distributed tracing end
    pass

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = _extract_correlation_id(event, context)
    trace_start(correlation_id)
    logger = logging.getLogger()  # Get module logger

    logger.info({
        "correlation_id": correlation_id,
        "event": event,
        "context": {
            "function_name": context.function_name if hasattr(context, 'function_name') else None,
            "aws_request_id": context.aws_request_id if hasattr(context, 'aws_request_id') else None
        }
    })

    response: Dict[str, Any] = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id
        },
        "body": ""
    }

    try:
        # Input validation & sanitization
        event = sanitize_input(event)

        # Example AWS SDK use: get parameter if SSM_CLIENT provided
        param_value = None
        if ssm_client:
            try:
                result = ssm_client.get_parameter(
                    Name=os.environ.get('EXAMPLE_PARAMETER_NAME', 'dummy_param'),
                    WithDecryption=True
                )
                param_value = result['Parameter']['Value']
            except (BotoCoreError, ClientError) as aws_err:
                logger.error(
                    {
                        "correlation_id": correlation_id,
                        "msg": f"SSM get_parameter failed: {aws_err}"
                    }
                )

        body = {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "correlation_id": correlation_id,
            "param_value": param_value
        }
        response["body"] = json.dumps(body)
        record_metric("lambda_success", 1)
    except Exception as ex:
        logger.error(
            {
                "correlation_id": correlation_id,
                "error": str(ex),
                "event": event
            }
        )
        response["statusCode"] = 500
        response["body"] = json.dumps({
            "message": f"Internal server error.",
            "correlation_id": correlation_id
        })
        record_metric("lambda_error", 1)
    finally:
        trace_end(correlation_id)
    return response

def _extract_correlation_id(event: Dict[str, Any], context: Any) -> str:
    # Try to get from event headers, fallback to context.aws_request_id, then random UUID
    headers = event.get('headers', {}) if isinstance(event, dict) else {}
    corr_id = None
    if headers and isinstance(headers, dict):
        corr_id = headers.get('X-Correlation-ID') or headers.get('x-correlation-id')
    if not corr_id and hasattr(context, 'aws_request_id'):
        corr_id = getattr(context, 'aws_request_id')
    if not corr_id:
        corr_id = str(uuid.uuid4())
    return corr_id

# For Serverless Framework v3: export as `handler`
handler = lambda_handler