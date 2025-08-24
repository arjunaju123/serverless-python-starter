import unittest
import logging
import uuid
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from handler import hello

# Setup structured logger
logger = logging.getLogger("test_handler")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(correlation_id)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_with_correlation(msg: str, level: int = logging.INFO, correlation_id: str = "") -> None:
    extra = {"correlation_id": correlation_id or "N/A"}
    logger.log(level, msg, extra=extra)

class HandlerTest(unittest.TestCase):

    def setUp(self) -> None:
        self.correlation_id = str(uuid.uuid4())
        log_with_correlation(f"Starting test with correlation ID: {self.correlation_id}", correlation_id=self.correlation_id)

    def tearDown(self) -> None:
        log_with_correlation(f"Finished test with correlation ID: {self.correlation_id}", correlation_id=self.correlation_id)

    def test_event_failsWithNumberAsEvent(self) -> None:
        try:
            # Input validation & sanitization
            event = 1
            context = 2
            if not isinstance(event, (dict, str, int, float)):
                raise ValueError(f"Invalid event type: {type(event)}")
            log_with_correlation(f"Testing hello handler with event: {event}", correlation_id=self.correlation_id)

            # Example resource usage with boto3 (cold start optimization)
            s3_client = boto3.client('s3')
            try:
                buckets = s3_client.list_buckets()
                log_with_correlation(f"S3 buckets enumerated: {len(buckets.get('Buckets', []))}", correlation_id=self.correlation_id)
            except (BotoCoreError, ClientError) as boto_exc:
                log_with_correlation(f"Boto3 error: {boto_exc}", logging.ERROR, self.correlation_id)
            finally:
                # No explicit cleanup required for boto3 clients

                pass

            response: Dict[str, Any] = hello(event, context)
            self.assertEqual(response.get('statusCode'), 200, f"Status code mismatch, correlation:{self.correlation_id}")
            self.assertTrue(isinstance(response.get('body'), str), f"Response body is not str, correlation:{self.correlation_id}")

            # Metrics and tracing (simple - replace with CloudWatch/Datadog integration in prod)
            log_with_correlation("Test assertion passed", correlation_id=self.correlation_id)
        except Exception as exc:
            log_with_correlation(f"Exception in test: {exc}", logging.ERROR, self.correlation_id)
            raise