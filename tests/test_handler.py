import unittest
import logging
import uuid
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from handler import hello

# Structured logging config
_LOG_FORMAT = (
    '{"level": "%(levelname)s", "correlation_id": "%(correlation_id)s", '
    '"message": "%(message)s", "module": "%(module)s", "lineno": %(lineno)d}'
)

class CorrelationIdAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return msg, {**kwargs, 'extra': {'correlation_id': self.extra['correlation_id']}}

def get_logger(correlation_id: str) -> logging.Logger:
    logger = logging.getLogger(f"HandlerTestLogger-{correlation_id}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(handler)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    return CorrelationIdAdapter(logger, {'correlation_id': correlation_id})

# Simulated metrics (would use CloudWatch/embedded metric format in production)
def record_metric(metric_name: str, value: float, correlation_id: str) -> None:
    logging.info(
        f'{{"metric": "{metric_name}", "value": {value}, "correlation_id": "{correlation_id}"}}',
        extra={"correlation_id": correlation_id}
    )

def validate_input(event: Any) -> None:
    if not isinstance(event, (dict, str, int, float)):
        raise ValueError("Event should be a dict, str, int, or float")

    # Further sanitization as needed

class HandlerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Pre-load AWS sessions/resources for cold start perf
        cls.aws_client = None
        try:
            cls.aws_client = boto3.client('sts')
        except (BotoCoreError, ClientError) as e:
            logging.error(
                f"Failed to initialize AWS client: {e}",
                extra={"correlation_id": "N/A"}
            )

    @classmethod
    def tearDownClass(cls) -> None:
        # Resource cleanup if necessary
        if cls.aws_client:
            del cls.aws_client
            cls.aws_client = None

    def test_event_failsWithNumberAsEvent(self) -> None:
        correlation_id = str(uuid.uuid4())
        logger = get_logger(correlation_id)
        try:
            # Simulate Lambda input validation and logging
            event = 1
            context = 2

            logger.info(
                f"Testing hello() with event={event}, context={context}",
                extra={"correlation_id": correlation_id}
            )

            try:
                validate_input(event)
            except ValueError as ve:
                logger.error(
                    f"Input validation error: {ve}",
                    extra={"correlation_id": correlation_id}
                )
                self.fail(f"Input validation failed: {ve}")

            # If needed, you can test AWS SDK connections
            if self.aws_client:
                try:
                    identity = self.aws_client.get_caller_identity()
                    logger.info(
                        f"AWS STS caller identity: {identity}",
                        extra={"correlation_id": correlation_id}
                    )
                    record_metric("aws_sts_calls", 1, correlation_id)
                except (BotoCoreError, ClientError) as err:
                    logger.error(
                        f"AWS SDK error: {err}",
                        extra={"correlation_id": correlation_id}
                    )

            # Call the Lambda handler
            response = None
            try:
                response = hello(event, context)
                record_metric("hello_calls", 1, correlation_id)
            except Exception as e:
                logger.error(
                    f"Error during hello(): {e}",
                    extra={"correlation_id": correlation_id}
                )
                self.fail(f"Exception in handler: {e}")

            # Observability: Log response and check
            logger.info(
                f"Handler response: {response}", extra={"correlation_id": correlation_id}
            )

            self.assertIsInstance(response, dict, f"Response is not a dict: {response}")
            self.assertEqual(response.get('statusCode'), 200, "statusCode is not 200")
            self.assertTrue(
                isinstance(response.get('body'), str),
                f"Response body is not a string: {response.get('body')}"
            )

        except Exception as test_exc:
            logger.error(
                f"Test error: {test_exc}",
                extra={"correlation_id": correlation_id}
            )
            raise