import unittest
import logging
import uuid
<<<<<<< Updated upstream
import os
from typing import Any, Dict
from unittest.mock import patch
=======
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError
>>>>>>> Stashed changes

# If AWS SDK needed:
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Observability Metrics/Tracing (Stub Example)
def record_metric(name: str, value: int = 1, correlation_id: str = '') -> None:
    logging.info(f'METRIC|{name}|{value}|correlation_id={correlation_id}')

def trace_event(event_name: str, details: Dict[str, Any], correlation_id: str = '') -> None:
    logging.info(f'TRACE|{event_name}|details={details}|correlation_id={correlation_id}')

# Setup structured logging early for cold start performance
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

def sanitize_input(data: Any) -> Any:
    # Example sanitization
    if isinstance(data, dict):
        return {str(k): str(v) for k, v in data.items()}
    if isinstance(data, (int, float, str)):
        return data
    return str(data)

def get_correlation_id(event: Any = None) -> str:
    cid = None
    if event and isinstance(event, dict):
        cid = event.get('correlationId')
        if not cid and 'headers' in event:
            # Try to extract from API Gateway Event
            cid = event['headers'].get('X-Correlation-Id')
    if not cid:
        cid = str(uuid.uuid4())
    return cid

# Mocked handler, in real scenario import from handler.py
def hello(event: Any, context: Any) -> Dict[str, Any]:
    correlation_id = get_correlation_id(event)
    logger.info(f'Handling hello event with correlation_id={correlation_id}')
    record_metric('hello_invocation', 1, correlation_id)
    trace_event('hello_called', {'event': str(event)}, correlation_id)
    try:
        sanitized_event = sanitize_input(event)
        # Simulate logic, in real code more security validation
        if not isinstance(event, (dict, int, float, str)):
            raise ValueError(f"Invalid event type: {type(event)}")
        response = {
            "statusCode": 200,
            "body": f"Hello, your event was: {sanitized_event}",
            "correlationId": correlation_id
        }
        return response
    except Exception as ex:
        logger.error(f'Error in hello handler: {ex}', exc_info=True, extra={'correlation_id': correlation_id})
        record_metric('hello_error', 1, correlation_id)
        return {
            "statusCode": 500,
            "body": "Internal server error",
            "correlationId": correlation_id
        }

logger = logging.getLogger("handler_test")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"event":"%(event)s","correlation_id":"%(correlation_id)s","level":"%(levelname)s","message":"%(message)s"}'
)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

def put_metric(metric_name: str, value: float = 1.0, correlation_id: str = '') -> None:
    try:
        client = boto3.client("cloudwatch")
        client.put_metric_data(
            Namespace="HandlerTest",
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": "Count",
                    "Dimensions": [
                        {"Name": "CorrelationId", "Value": correlation_id},
                    ],
                }
            ],
        )
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to put metric: {e}", extra={"event": "put_metric", "correlation_id": correlation_id})

def validate_input(event: Any, context: Any, correlation_id: str) -> None:
    if not isinstance(event, (dict, int, str, float, type(None))):
        logger.warning(
            f"Unsupported input type: {type(event)}",
            extra={"event": "input_validation", "correlation_id": correlation_id}
        )
        raise ValueError("Unsupported input type")

class HandlerTest(unittest.TestCase):

<<<<<<< Updated upstream
    @patch('handler.hello', side_effect=hello)
    def test_event_failsWithNumberAsEvent(self, mock_hello):
        correlation_id = get_correlation_id(1)
        try:
            # Input validation
            event = 1
            context = 2
            response = hello(event, context)
            self.assertEqual(response.get('statusCode'), 200)
            self.assertTrue(isinstance(response.get('body'), str))
            # Log test case with correlation id for traceability
            logger.info(f'Test test_event_failsWithNumberAsEvent succeeded', extra={'correlation_id': correlation_id})
            record_metric('test_event_failsWithNumberAsEvent_success', 1, correlation_id)
        except Exception as ex:
            logger.error(f"Test test_event_failsWithNumberAsEvent failed: {ex}", exc_info=True, extra={'correlation_id': correlation_id})
            record_metric('test_event_failsWithNumberAsEvent_error', 1, correlation_id)
            raise

    @classmethod
    def tearDownClass(cls):
        # Clean up any AWS resources if used
        try:
            # Example: close any boto3 clients if needed (they are normally stateless)
            pass
        except (BotoCoreError, ClientError) as ex:
            logger.error(f"Resource cleanup error: {ex}")

if __name__ == '__main__':
    unittest.main()
=======
    def setUp(self) -> None:
        self.correlation_id = str(uuid.uuid4())

    def tearDown(self) -> None:
        pass  # Any resource cleanup if needed

    def test_event_failsWithNumberAsEvent(self) -> None:
        event = 1
        context = 2
        try:
            validate_input(event, context, self.correlation_id)
            logger.info(
                f"Calling hello handler",
                extra={"event": "call_handler", "correlation_id": self.correlation_id}
            )
            response: Dict[str, Any] = hello(event, context)
            put_metric("HandlerTestSuccess", 1, self.correlation_id)
            self.assertEqual(response.get("statusCode"), 200)
            self.assertIsInstance(response.get("body"), str)
        except Exception as exc:
            put_metric("HandlerTestFailure", 1, self.correlation_id)
            logger.exception(
                f"Exception occurred during test_event_failsWithNumberAsEvent: {exc}",
                extra={"event": "exception", "correlation_id": self.correlation_id}
            )
            self.fail(f"Exception occurred during test_event_failsWithNumberAsEvent: {exc}")
>>>>>>> Stashed changes
