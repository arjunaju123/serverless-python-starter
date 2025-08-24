import unittest
import logging
import uuid
import traceback
from typing import Any, Dict
import json

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from handler import hello

# Configure logging for Lambda best practices
logger = logging.getLogger("handler_test")
logger.setLevel(logging.INFO)

def get_correlation_id(event: Any) -> str:
    """
    Extract or generate a correlation ID for logging/tracing.
    """
    if isinstance(event, dict):
        return event.get("headers", {}).get("X-Correlation-Id", str(uuid.uuid4()))
    return str(uuid.uuid4())

def sanitize_input(event: Any) -> Any:
    """
    Basic sanitization of the input event.
    """
    if isinstance(event, dict):
        try:
            # JSON-serializable check
            json.dumps(event)
        except Exception:
            raise ValueError("Event is not JSON serializable.")
        return event
    elif isinstance(event, (str, int, float, bool)):
        return event
    else:
        raise ValueError("Input event is not a supported type.")

class HandlerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize AWS resources with lazy connection for performance
        cls.dynamodb_resource = None
        cls._metrics_client = None

    @classmethod
    def tearDownClass(cls):
        # Cleanup connections if any
        if cls.dynamodb_resource is not None:
            del cls.dynamodb_resource
        if cls._metrics_client is not None:
            del cls._metrics_client

    def _get_dynamodb_resource(self):
        """Lazy initialized for performance"""
        if not self.dynamodb_resource:
            try:
                self.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
            except (BotoCoreError, ClientError) as e:
                logger.error(f"Failed to establish DynamoDB resource: {e}", exc_info=True)
                raise
        return self.dynamodb_resource

    def _get_metrics_client(self):
        """Example: cloudwatch metrics client for observability"""
        if not self._metrics_client:
            try:
                self._metrics_client = boto3.client("cloudwatch", region_name="us-east-1")
            except (BotoCoreError, ClientError) as e:
                logger.error(f"Failed to establish CloudWatch client: {e}", exc_info=True)
                raise
        return self._metrics_client

    def publish_metric(self, name: str, value: float, correlation_id: str):
        """Publish a custom metric (example for observability)"""
        client = self._get_metrics_client()
        try:
            client.put_metric_data(
                Namespace="MyApp/HandlerTest",
                MetricData=[
                    {
                        "MetricName": name,
                        "Value": value,
                        "Unit": "Count",
                        "Dimensions": [
                            {"Name": "TestCase", "Value": self._testMethodName},
                            {"Name": "CorrelationId", "Value": correlation_id}
                        ]
                    }
                ]
            )
        except (BotoCoreError, ClientError) as e:
            logger.warning(f"Metric '{name}' publish failed: {e}")

    def test_event_failsWithNumberAsEvent(self):
        correlation_id = str(uuid.uuid4())
        event = 1
        context = 2
        try:
            sanitized_event = sanitize_input(event)
            response: Dict[str, Any] = hello(sanitized_event, context)
            logger.info(
                f"Test 'test_event_failsWithNumberAsEvent' succeeded",
                extra={"correlation_id": correlation_id, "event": sanitized_event}
            )
            self.publish_metric("TestSuccess", 1, correlation_id)
        except Exception as exc:
            logger.error(
                f"Test 'test_event_failsWithNumberAsEvent' failed: {exc}\n{traceback.format_exc()}",
                extra={"correlation_id": correlation_id, "event": event}
            )
            self.publish_metric("TestFailure", 1, correlation_id)
            raise

        # Input validation for security
        self.assertIsInstance(response, dict, f"Response must be dict, got {type(response)}")

        status_code = response.get('statusCode')
        self.assertEqual(
            status_code, 200,
            f"Expected statusCode 200 but got {status_code} (correlation_id={correlation_id})"
        )
        body = response.get('body')
        self.assertIsInstance(
            body, str,
            f"Response 'body' must be str, got {type(body)} (correlation_id={correlation_id})"
        )