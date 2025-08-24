import json
import logging
import os
<<<<<<< Updated upstream
<<<<<<< Updated upstream
import sys
=======
import traceback
>>>>>>> Stashed changes
import uuid
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

<<<<<<< Updated upstream
# Cold start global initialization
logger = logging.getLogger()
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '{"timestamp":"%(asctime)s", "level":"%(levelname)s", "correlation_id":"%(correlation_id)s", "message":"%(message)s"}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def get_correlation_id(event: Dict[str, Any]) -> str:
    headers = event.get('headers') or {}
    return (
        headers.get('X-Correlation-Id')
        or event.get('requestContext', {}).get('requestId')
        or str(uuid.uuid4())
    )

def log_with_correlation(level: int, message: str, correlation_id: str) -> None:
    extra = {'correlation_id': correlation_id}
    logger.log(level, message, extra=extra)

def sanitize_message(message: str) -> str:
    if not isinstance(message, str):
        return "Invalid message type."
    # Basic sanitization; more may be needed for other data
    return message.replace("\n", " ").replace("\r", " ")

def validate_event(event: Dict[str, Any]) -> bool:
    if not isinstance(event, dict):
        return False
    return True

def record_metric(metric_name: str, value: float, correlation_id: str) -> None:
    # Placeholder for metrics; integrate with CloudWatch Embedded Metrics as needed
    log_with_correlation(logging.INFO, f"METRIC {metric_name}: {value}", correlation_id)

def trace_execution(context: Any, correlation_id: str) -> None:
    # Placeholder for integration with AWS X-Ray or other tracing tools
    log_with_correlation(logging.INFO, f"TRACE start - aws_request_id: {getattr(context, 'aws_request_id', '')}", correlation_id)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    trace_execution(context, correlation_id)
    record_metric("lambda_invocation", 1, correlation_id)

    try:
        if not validate_event(event):
            log_with_correlation(logging.ERROR, "Invalid event received", correlation_id)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Bad Request"}),
                "headers": {"X-Correlation-Id": correlation_id}
            }

        # Example boto3 usage with error handling
        try:
            # Demonstrating cold-start optimized resource
            s3_client = boto3.client('s3')
            # List buckets to illustrate AWS SDK pattern
            response = s3_client.list_buckets()
            bucket_names = [sanitize_message(b.get('Name', '')) for b in response.get('Buckets', [])]
        except (BotoCoreError, ClientError) as aws_error:
            log_with_correlation(logging.ERROR, f"AWS SDK error: {aws_error}", correlation_id)
            bucket_names = []

        body = {
            "message": sanitize_message("Go Serverless v1.0! Your function executed successfully!"),
            "buckets": bucket_names,
            "correlation_id": correlation_id
        }

        log_with_correlation(logging.INFO, "Function executed successfully", correlation_id)
        record_metric("lambda_success", 1, correlation_id)
        return {
            "statusCode": 200,
            "body": json.dumps(body),
            "headers": {"X-Correlation-Id": correlation_id}
        }
    except Exception as ex:
        log_with_correlation(logging.ERROR, f"Unhandled exception: {ex}", correlation_id)
        record_metric("lambda_error", 1, correlation_id)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal Server Error", "correlation_id": correlation_id}),
            "headers": {"X-Correlation-Id": correlation_id}
=======
# Initialize logger at module load for cold start optimization
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def sanitize_input(event: Dict[str, Any]) -> Dict[str, Any]:
    # Basic sanitization: ensure event is dict and has expected keys
    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary.")
    for key in event.keys():
        if not isinstance(key, str):
            raise ValueError(f"Invalid key type: {type(key)}")
    return event

def create_correlation_id(event: Dict[str, Any]) -> str:
    # Extract correlation ID from event or generate new
    correlation_id = (
        event.get("headers", {}).get("X-Correlation-Id") or
        event.get("requestContext", {}).get("requestId") or
=======
import uuid
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from typing import Any, Dict

# Optimize logger creation for cold start
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)

# Metrics (CloudWatch Embedded Metric Format)
def log_metrics(correlation_id: str, success: bool) -> None:
    metrics = {
        "_aws": {
            "Timestamp": int(round(__import__('time').time() * 1000)),
            "CloudWatchMetrics": [
                {
                    "Namespace": "ServerlessApp",
                    "Dimensions": [["FunctionName"]],
                    "Metrics": [
                        {"Name": "SuccessfulInvocation", "Unit": "Count"},
                        {"Name": "FailedInvocation", "Unit": "Count"}
                    ]
                }
            ]
        },
        "FunctionName": os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'Unspecified'),
        "SuccessfulInvocation": int(success),
        "FailedInvocation": int(not success),
        "CorrelationId": correlation_id
    }
    print(json.dumps(metrics)) # CloudWatch EMF logs

def get_correlation_id(event: Dict[str, Any]) -> str:
    headers = event.get('headers', {})
    correlation_id = (
        headers.get('X-Correlation-Id') or
        event.get('requestContext', {}).get('requestId') or
>>>>>>> Stashed changes
        str(uuid.uuid4())
    )
    return correlation_id

<<<<<<< Updated upstream
def record_metric(metric_name: str, value: int = 1) -> None:
    # Example metric recording (CloudWatch Embedded Metric Format)
    try:
        print(json.dumps({
            "_aws": {
                "Timestamp": int(os.environ.get("AWS_LAMBDA_FUNCTION_START_TIME", "0")) or 0,
                "CloudWatchMetrics": [
                    {
                        "Namespace": "ServerlessApp",
                        "Dimensions": ["FunctionName"],
                        "Metrics": [{"Name": metric_name, "Unit": "Count"}]
                    }
                ]
            },
            "FunctionName": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "Unknown"),
            metric_name: value
        }))
    except Exception as e:
        logger.warning(f"Metric recording failed: {e}")

def hello(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = create_correlation_id(event)
    logger.info(f"Request received, correlation_id={correlation_id}")
    record_metric("InvocationCount", 1)
    try:
        safe_event = sanitize_input(event)

        # Example AWS SDK usage (boto3, e.g., get current AWS account)
        client = boto3.client("sts")
        try:
            identity = client.get_caller_identity()
            account_id = identity.get("Account")
        except (BotoCoreError, ClientError) as aws_err:
            logger.error(f"AWS error (correlation_id={correlation_id}): {aws_err}")
            account_id = "Unknown"
        finally:
            client.close() if hasattr(client, "close") else None  # For resource cleanup

        body = {
            "message": (
                "Go Serverless v3.0! Your function executed successfully!"
            ),
            "correlation_id": correlation_id,
            "account_id": account_id,
        }

        logger.info(
            f"Response success (correlation_id={correlation_id}) "
            f"body={body}"
        )
        record_metric("SuccessCount", 1)
        return {
            "statusCode": 200,
            "body": json.dumps(body)
        }

    except Exception as exc:
        err_trace = traceback.format_exc()
        logger.error(
            f"Unhandled exception (correlation_id={correlation_id}): {exc}",
            extra={"traceback": err_trace}
        )
        record_metric("ErrorCount", 1)
        error_body = {
            "error": "Internal Server Error",
            "correlation_id": correlation_id,
            "details": str(exc),
        }
        return {
            "statusCode": 500,
            "body": json.dumps(error_body)
>>>>>>> Stashed changes
        }
=======
def validate_event(event: Dict[str, Any]) -> None:
    # Example: Validate required keys. Extend as needed.
    if not isinstance(event, dict):
        raise ValueError("Invalid event format: Expected a dictionary.")
    # Further input validation can be added here

def hello(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    logger.info(f"Function invoked. CorrelationId={correlation_id}")

    # Security: input validation & sanitization
    try:
        validate_event(event)
    except Exception as ve:
        logger.error(f"Validation error. CorrelationId={correlation_id} Error={ve}")
        log_metrics(correlation_id, success=False)
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Invalid input.",
                "correlationId": correlation_id
            })
        }
    # Tracing: Example with AWS X-Ray if available (no-op if not)
    try:
        from aws_xray_sdk.core import patch_all
        patch_all()  # Patch boto3, requests, etc. for tracing
    except ImportError:
        pass

    # Sample AWS SDK interaction, e.g., describe Lambda function (replace with real usage)
    boto3_client = None
    try:
        boto3_client = boto3.client('lambda')
        function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', '')
        if function_name:
            response = boto3_client.get_function(FunctionName=function_name)
            logger.info(f"Retrieved function info. CorrelationId={correlation_id}")
        # Close the client if necessary
        # boto3 clients do not require explicit close but for resource APIs like DynamoDB this would change
    except (BotoCoreError, ClientError) as aws_err:
        logger.error(f"AWS SDK error. CorrelationId={correlation_id} Error={aws_err}")
        log_metrics(correlation_id, success=False)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal AWS error.",
                "correlationId": correlation_id
            })
        }
    except Exception as ex:
        logger.error(f"Unexpected error. CorrelationId={correlation_id} Error={ex}")
        log_metrics(correlation_id, success=False)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Unexpected error.",
                "correlationId": correlation_id
            })
        }

    # Observability: record success metric
    log_metrics(correlation_id, success=True)
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "correlationId": correlation_id
    }
    logger.info(f"Function succeeded. CorrelationId={correlation_id}")
    return {
        "statusCode": 200,
        "body": json.dumps(body)
    }
>>>>>>> Stashed changes
