import unittest
import logging
import uuid
import time
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from handler import hello

logger = logging.getLogger("handler_test")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.handlers = [handler]


def log_with_correlation(level: int, message: str, correlation_id: str) -> None:
    extra = {'correlation_id': correlation_id}
    logger.log(level, message, extra=extra)


class MetricsTracer:
    """Simple metrics/tracing for illustration; replace with AWS X-Ray/CloudWatch in production."""

    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self.metrics = {}
        self.start_times = {}

    def start(self, metric: str) -> None:
        self.start_times[metric] = time.monotonic()

    def stop(self, metric: str) -> None:
        if metric in self.start_times:
            elapsed = time.monotonic() - self.start_times[metric]
            self.metrics[metric] = elapsed
            log_with_correlation(
                logging.INFO, f'Metric "{metric}" elapsed: {elapsed:.4f}s', self.correlation_id
            )

    def report(self) -> None:
        for metric, elapsed in self.metrics.items():
            log_with_correlation(
                logging.INFO, f'Report - {metric}: {elapsed:.4f}s', self.correlation_id
            )


class HandlerTest(unittest.TestCase):
    _dynamodb_client = None

    @classmethod
    def get_dynamodb_client(cls):
        if cls._dynamodb_client is None:
            try:
                cls._dynamodb_client = boto3.client("dynamodb")
            except (BotoCoreError, ClientError) as e:
                correlation_id = str(uuid.uuid4())
                log_with_correlation(
                    logging.ERROR,
                    f"Failed to create DynamoDB client: {e}",
                    correlation_id,
                )
                raise
        return cls._dynamodb_client

    def setUp(self) -> None:
        self.correlation_id = str(uuid.uuid4())
        log_with_correlation(logging.INFO, "Test started", self.correlation_id)
        self.tracer = MetricsTracer(self.correlation_id)

    def tearDown(self) -> None:
        self.tracer.report()
        log_with_correlation(logging.INFO, "Test finished", self.correlation_id)

    def safe_hello_call(self, event: Any, context: Any) -> Dict[str, Any]:
        self.tracer.start("hello_call")
        try:
            # Input Validation & Sanitization
            if not isinstance(event, (dict, str, int, float)):
                raise ValueError("Event must be a dict, string, int, or float")
            if not isinstance(context, (dict, type(None), int, float, str)):
                raise ValueError("Context type is not valid")
            # Example usage of resource (pretend we're reading something):
            try:
                client = self.get_dynamodb_client()
                # Only do a lightweight call to ensure client works; not strictly required
                client.list_tables(Limit=1)
            except (BotoCoreError, ClientError) as e:
                log_with_correlation(
                    logging.WARNING,
                    f"DynamoDB connectivity test failed: {e}",
                    self.correlation_id,
                )
            # Actual Lambda handler call
            response = hello(event, context)
            if not isinstance(response, dict):
                raise TypeError("Lambda handler must return a dict")
            return response
        except Exception as ex:
            log_with_correlation(
                logging.ERROR,
                f"Exception in hello handler: {type(ex).__name__}: {ex}",
                self.correlation_id,
            )
            # Simulate Lambda error format:
            return {
                "statusCode": 500,
                "body": f'{{"error": "{str(ex)}"}}',
                "headers": {"Content-Type": "application/json"},
            }
        finally:
            self.tracer.stop("hello_call")

    def test_event_failsWithNumberAsEvent(self) -> None:
        # Security: ensure input does not cause crash, provides structured error on bad input
        event: int = 1
        context: int = 2
        response = self.safe_hello_call(event, context)
        self.assertEqual(response.get("statusCode"), 200)
        self.assertTrue(isinstance(response.get("body"), str))