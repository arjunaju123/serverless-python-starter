import unittest
import uuid
import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Set up structured logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.handlers = [handler]

def get_correlation_id(event: Any = None) -> str:
    if isinstance(event, dict) and 'headers' in event:
        return event['headers'].get('X-Correlation-Id', str(uuid.uuid4()))
    return str(uuid.uuid4())

def validate_and_sanitize(event: Any) -> Dict[str, Any]:
    # Example sanitization, expand as needed
    if not isinstance(event, dict):
        raise ValueError("Input 'event' must be a dictionary")
    return event

def record_metric(metric_name: str, value: float, correlation_id: str) -> None:
    try:
        client = boto3.client('cloudwatch')
        client.put_metric_data(
            Namespace='HelloLambda',
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': 'Count',
                    'Dimensions': [{'Name': 'CorrelationId', 'Value': correlation_id}]
                }
            ]
        )
    except (BotoCoreError, ClientError) as e:
        logger.error(f'Failed to publish metric {metric_name}: {e}', extra={'correlation_id': correlation_id})

def hello(event: Any, context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    try:
        logger.info('Received event', extra={'correlation_id': correlation_id})
        sanitized_event = validate_and_sanitize(event)
        # Main handler logic here
        result = {"message": "Hello, world!"}
        response = {
            "statusCode": 200,
            "body": str(result)
        }
        record_metric('HelloSuccess', 1, correlation_id)
        logger.info('Handler succeeded', extra={'correlation_id': correlation_id})
        return response
    except ValueError as ve:
        logger.error(f'Input validation error: {ve}', extra={'correlation_id': correlation_id})
        record_metric('HelloValidationError', 1, correlation_id)
        return {
            "statusCode": 400,
            "body": f"Input validation error: {ve}"
        }
    except Exception as ex:
        logger.exception('Unhandled exception', extra={'correlation_id': correlation_id})
        record_metric('HelloUnhandledException', 1, correlation_id)
        return {
            "statusCode": 500,
            "body": "Internal server error"
        }

class HandlerTest(unittest.TestCase):
    def test_event_failsWithNumberAsEvent(self) -> None:
        # Mimic actual Lambda event structure in the test for accuracy
        event = 1  # Intentionally invalid to test error handling
        context = 2  # Mock context
        response = hello(event, context)
        self.assertEqual(response.get('statusCode'), 400)
        self.assertTrue(isinstance(response.get('body'), str))