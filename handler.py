import json
import logging
from typing import Any, Dict
import uuid
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    session = boto3.Session()
    ssm_client = session.client('ssm')
except Exception as e:
    logger.error(f"Failed during cold start boto3 initialization: {e}", exc_info=True)
    ssm_client = None

def get_correlation_id(event: Dict[str, Any]) -> str:
    if isinstance(event, dict):
        headers = event.get('headers', {}) or {}
        req_id = headers.get('X-Correlation-ID') or headers.get('x-correlation-id')
        if req_id and isinstance(req_id, str):
            return req_id
    return str(uuid.uuid4())

def validate_event(event: Dict[str, Any]) -> bool:
    # Minimal input validation example, extend as needed
    if not isinstance(event, dict):
        return False
    return True

def hello(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    logger.info(f"Lambda invoked. CorrelationId={correlation_id}", extra={'correlation_id': correlation_id})

    if not validate_event(event):
        logger.warning(f"Invalid event: {event}", extra={'correlation_id': correlation_id})
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid input", "correlationId": correlation_id})
        }

    try:
        # Example of a boto3 SDK call for metrics/observability
        parameter_name = "/example/param"
        param_value = None
        if ssm_client:
            try:
                response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=False)
                param_value = response.get('Parameter', {}).get('Value')
                logger.info(
                    f"Retrieved parameter value from SSM.", 
                    extra={'parameter': parameter_name, 'correlation_id': correlation_id}
                )
            except (BotoCoreError, ClientError) as e:
                logger.error(
                    f"Failed to get parameter from SSM: {e}", 
                    exc_info=True, 
                    extra={'parameter': parameter_name, 'correlation_id': correlation_id}
                )
        else:
            logger.warning(
                "SSM client not initialized. Skipping SSM call.", 
                extra={'correlation_id': correlation_id}
            )

        # Observability: Simple return metric via log
        logger.info(
            "Lambda hello() executed successfully.",
            extra={'correlation_id': correlation_id, 'success': True}
        )

        body = {
            "message": f"Go Serverless v1.0! Your function executed successfully!",
            "correlationId": correlation_id,
            "ssmParameter": param_value
        }
        return {
            "statusCode": 200,
            "body": json.dumps(body)
        }

    except Exception as e:
        logger.error(
            f"Error processing event: {e}", 
            exc_info=True, 
            extra={'correlation_id': correlation_id}
        )
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "correlationId": correlation_id})
        }