import json
import logging
import uuid
import sys
from typing import Any, Dict

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    # boto3 might be excluded in some local test invocations
    boto3 = None


# Global logger setup for cold start optimization
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _extract_correlation_id(event: Dict[str, Any]) -> str:
    headers = event.get("headers", {}) if isinstance(event, dict) else {}
    # Common header for correlation: "X-Correlation-Id"
    correlation_id = headers.get("X-Correlation-Id") or headers.get("x-correlation-id")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    return correlation_id


def _sanitize_input(event: Dict[str, Any]) -> Dict[str, Any]:
    # Basic input validation/sanitization
    if not isinstance(event, dict):
        return {}
    # Whitelist allowed keys (if known), else shallow copy
    allowed_keys = {"headers", "body", "pathParameters", "queryStringParameters"}
    return {k: v for k, v in event.items() if k in allowed_keys}


def _log_structured(level: int, message: str, correlation_id: str, **kwargs):
    extra = {"correlation_id": correlation_id}
    logger.log(level, message, extra=extra, **kwargs)


def _capture_metrics(correlation_id: str, success: bool = True):
    # Simulate metrics; replace with real metrics library as needed
    logger.info(
        f"{{'metric': 'lambda_invocation', 'success': {success}, 'correlation_id': '{correlation_id}'}}",
        extra={"correlation_id": correlation_id},
    )


def _capture_trace(event: Dict[str, Any], context: Any, correlation_id: str):
    # Placeholder for request tracing (X-Ray, OpenTelemetry, etc.)
    logger.debug(
        f"{{'trace': 'lambda_invocation', 'event': {event}, 'context': str(context), 'correlation_id': '{correlation_id}'}}",
        extra={"correlation_id": correlation_id}
    )


def hello(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = _extract_correlation_id(event)
    _log_structured(logging.INFO, "Lambda invocation started.", correlation_id)

    _capture_trace(event, context, correlation_id)

    try:
        sanitized_event = _sanitize_input(event)

        # Example AWS SDK usage; replace 'sts' as needed
        response_data = None
        if boto3:
            try:
                sts_client = boto3.client("sts")
                identity = sts_client.get_caller_identity()
                response_data = {
                    "aws_account": identity.get("Account"),
                    "user_arn": identity.get("Arn"),
                }
            except (BotoCoreError, ClientError) as sdk_ex:
                _log_structured(logging.ERROR, f"AWS SDK error: {sdk_ex}", correlation_id)
                response_data = {"aws_error": str(sdk_ex)}

        body = {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "correlationId": correlation_id,
        }
        if response_data:
            body.update(response_data)

        _capture_metrics(correlation_id, success=True)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id,
            },
            "body": json.dumps(body),
        }

    except Exception as ex:
        _log_structured(logging.ERROR, f"Unhandled exception: {ex}", correlation_id)
        _capture_metrics(correlation_id, success=False)

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-Id": correlation_id,
            },
            "body": json.dumps({
                "error": "InternalServerError",
                "message": f"An error occurred: {str(ex)}",
                "correlationId": correlation_id,
            }),
        }