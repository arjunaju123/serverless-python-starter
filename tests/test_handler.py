import unittest
import logging
import uuid
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from handler import hello

# Structured logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

class ContextualAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        correlation_id = kwargs.pop("correlation_id", getattr(self, "correlation_id", "N/A"))
        return msg, {"extra": {"correlation_id": correlation_id}}

def get_correlation_id() -> str:
    return str(uuid.uuid4())

def validate_event(event: Any) -> None:
    if not isinstance(event, (dict, int, float, str)):
        raise ValueError(f"Invalid event type: {type(event)}")

class HandlerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.correlation_id = get_correlation_id()
        cls.logger = ContextualAdapter(logger, {"correlation_id": cls.correlation_id})
        try:
            # Performance: instantiate boto3 client only if needed
            cls.lambda_client = boto3.client("lambda")
            cls.logger.info("Initialized boto3 Lambda client", correlation_id=cls.correlation_id)
        except (BotoCoreError, ClientError) as e:
            cls.logger.error(f"Failed to initialize boto3 Lambda client: {e}", correlation_id=cls.correlation_id)
            cls.lambda_client = None

    @classmethod
    def tearDownClass(cls):
        # Clean up boto3 client if needed (no explicit cleanup generally required)
        cls.logger.info("Test class teardown complete", correlation_id=cls.correlation_id)
        cls.lambda_client = None

    def test_event_failsWithNumberAsEvent(self) -> None:
        correlation_id = get_correlation_id()
        logger = ContextualAdapter(logger, {"correlation_id": correlation_id})

        event = 1
        context = 2  # Context stub
        try:
            validate_event(event)
        except ValueError as ve:
            logger.error(f"Input validation failed: {ve}", correlation_id=correlation_id)
            self.fail(f"Input validation failed: {ve}")

        try:
            # Lambda handler pattern; ensure context is passed if needed
            response: Dict[str, Any] = hello(event, context)
            body = response.get('body')
            status_code = response.get('statusCode')

            # Observability: log test step
            logger.info(f"Lambda returned statusCode={status_code}", correlation_id=correlation_id)

            # Test assertions
            self.assertEqual(status_code, 200, "Expected statusCode to be 200")
            self.assertIsInstance(body, str, "Expected body to be a string")

            # Metrics/tracing (simulate)
            logger.info(f"Test passed for event={event}", correlation_id=correlation_id)
        except Exception as e:
            logger.error(f"Exception during Lambda invocation: {e}", correlation_id=correlation_id)
            self.fail(f"Lambda invocation failed with exception: {e}")