import json
import logging
import os
import boto3
import traceback
import uuid
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    # Initialize AWS clients outside handler for cold start optimization
    ssm_client = boto3.client('ssm')
except Exception as init_exc:
    logger.error(f"Error initializing boto3 clients: {init_exc}")
    ssm_client = None

def validate_event(event: Dict[str, Any]) -> bool:
    # Example: Validate required fields or types
    if not isinstance(event, dict):
        return False
    # In a real API, check specific keys here if needed
    return True

def hello(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = _extract_correlation_id(event)
    _put_correlation_id_to_logs(correlation_id)

    try:
        if not validate_event(event):
            _log_metric('InvalidEvent', correlation_id)
            return _response(
                400, {"error": "Invalid event format."}, correlation_id
            )

        # Example AWS SDK call with error handling (SSM GetParameter)
        parameter_name = os.environ.get("EXAMPLE_SSM_PARAM", "example/param")
        ssm_parameter = None
        if ssm_client is not None:
            try:
                ssm_resp = ssm_client.get_parameter(
                    Name=parameter_name,
                    WithDecryption=True
                )
                ssm_parameter = ssm_resp['Parameter']['Value']
            except ssm_client.exceptions.ParameterNotFound:
                logger.warning(f"SSM parameter '{parameter_name}' not found", extra={"correlation_id": correlation_id})
            except Exception as aws_exc:
                logger.error(f"SSM get_parameter failed: {aws_exc}", extra={"correlation_id": correlation_id})

        _log_metric('Success', correlation_id)
        _log_trace('hello_function_called', correlation_id)

        body = {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "correlation_id": correlation_id,
            "ssm_parameter": ssm_parameter
        }

        return _response(200, body, correlation_id)

    except Exception as exc:
        logger.error(
            f"Unhandled exception: {exc}",
            extra={"correlation_id": correlation_id, "traceback": traceback.format_exc()}
        )
        _log_metric('Error', correlation_id)
        return _response(
            500, {"error": "Internal server error"}, correlation_id
        )

def _response(status_code: int, body: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
    sanitized_body = {k: _sanitize(v) for k, v in body.items()}
    return {
        "statusCode": status_code,
        "body": json.dumps(sanitized_body),
        "headers": {
            "Content-Type": "application/json",
            "X-Correlation-Id": correlation_id
        }
    }

def _sanitize(value: Any) -> Any:
    # Example sanitization logic
    if isinstance(value, str):
        return value.replace("<", "&lt;").replace(">", "&gt;")
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    return value

def _extract_correlation_id(event: Dict[str, Any]) -> str:
    # Try extracting from event headers, else generate
    headers = event.get("headers") if isinstance(event.get("headers"), dict) else {}
    correlation_id = headers.get("X-Correlation-Id") or str(uuid.uuid4())
    return correlation_id

def _put_correlation_id_to_logs(correlation_id: str) -> None:
    logger.info(f"Request correlation_id: {correlation_id}", extra={"correlation_id": correlation_id})

def _log_metric(metric_name: str, correlation_id: str) -> None:
    logger.info(f"Metric: {metric_name}", extra={"correlation_id": correlation_id})

def _log_trace(trace_name: str, correlation_id: str) -> None:
    logger.info(f"Trace: {trace_name}", extra={"correlation_id": correlation_id})