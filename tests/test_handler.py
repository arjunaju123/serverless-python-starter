import unittest
import logging
<<<<<<< Updated upstream
import os
from typing import Any, Dict
import uuid
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from handler import hello

# Setup structured logger
logger = logging.getLogger(__name__)
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.setLevel(log_level)
handler_stream = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "correlation_id": "%(correlation_id)s"}'
)
handler_stream.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler_stream)

# For observability
def add_correlation_id(record, correlation_id: str) -> None:
    setattr(record, "correlation_id", correlation_id)
=======
import uuid
from typing import Any, Dict

from handler import hello

# Structured logger setup
logger = logging.getLogger("HandlerTest")
logger.setLevel(logging.INFO)
handler_stream = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "correlationId": "%(correlationId)s", "message": "%(message)s"}'
)
handler_stream.setFormatter(formatter)
logger.addHandler(handler_stream)

# Context manager for boto3 and other resources can be added here if needed in integration tests

def log_with_correlation_id(correlation_id: str, msg: str, level: int = logging.INFO) -> None:
    extra = {'correlationId': correlation_id}
    logger.log(level, msg, extra=extra)
>>>>>>> Stashed changes

class HandlerTest(unittest.TestCase):

    def setUp(self) -> None:
<<<<<<< Updated upstream
        # Generate a unique correlation ID (for tracing/observability)
        self.correlation_id = str(uuid.uuid4())
        # Add it to log records
        logging.Logger.makeRecord_orig = logging.Logger.makeRecord
        def makeRecord_patch(logger, *args, **kwargs):
            record = logging.Logger.makeRecord_orig(logger, *args, **kwargs)
            add_correlation_id(record, self.correlation_id)
            return record
        logging.Logger.makeRecord = makeRecord_patch

        # Metrics/stats placeholder (could be exported to CloudWatch)
        self.metrics = {"test_runs": 0, "failures": 0}

        # Prepare mock AWS resources if needed
        self.ssm_client = None
        try:
            self.ssm_client = boto3.client("ssm")
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error initializing boto3 SSM client: {e}")

    def tearDown(self) -> None:
        # Clean up/make record original again for other tests
        if hasattr(logging.Logger, "makeRecord_orig"):
            logging.Logger.makeRecord = logging.Logger.makeRecord_orig
            del logging.Logger.makeRecord_orig

        # Metrics/cleanup placeholder
        self.metrics["test_runs"] += 1

        # AWS resource cleanup if necessary
        self.ssm_client = None

    def test_event_failsWithNumberAsEvent(self) -> None:
        # Observability: trace the test case
        logger.info(f"Starting test_event_failsWithNumberAsEvent", extra={"correlation_id": self.correlation_id})
        try:
            # Input validation
            event: Any = 1
            context: Any = 2
            # Security: sanitize event
            if not isinstance(event, (dict, str, int, float)):
                raise ValueError("Invalid event type provided to Lambda handler")
            if hasattr(event, "__class__") and event.__class__.__module__ == 'builtins':
                pass  # OK
            else:
                logger.warning("Event type is not a built-in type", extra={"correlation_id": self.correlation_id})

            response: Dict[str, Any] = hello(event, context)
            # Observability: add metric
            logger.info(f"Handler response: {response}", extra={"correlation_id": self.correlation_id})
            self.assertEqual(response.get('statusCode'), 200)
            self.assertTrue(isinstance(response.get('body'), str))
        except AssertionError as ae:
            self.metrics["failures"] += 1
            logger.error(f"Assertion failed in test_event_failsWithNumberAsEvent: {ae}", extra={"correlation_id": self.correlation_id})
            raise  # Let unittest catch the failure
        except Exception as e:
            self.metrics["failures"] += 1
            logger.error(f"Unexpected error in test_event_failsWithNumberAsEvent: {e}", extra={"correlation_id": self.correlation_id})
            raise

        # Metric/trace: log successful completion
        logger.info(f"Completed test_event_failsWithNumberAsEvent", extra={"correlation_id": self.correlation_id})
=======
        # Generates a correlation ID per test
        self.correlation_id = str(uuid.uuid4())
        log_with_correlation_id(self.correlation_id, f"Starting test case: {self._testMethodName}")

    def tearDown(self) -> None:
        log_with_correlation_id(self.correlation_id, f"Finished test case: {self._testMethodName}")

    def test_event_failsWithNumberAsEvent(self) -> None:
        event = 1
        context = 2

        # Input validation
        if not isinstance(event, (dict, str, int)):
            log_with_correlation_id(self.correlation_id, "Invalid event type", logging.ERROR)
            self.fail("Invalid event type passed to Lambda handler.")

        # Metrics/Tracing stub (could be replaced with AWS Embedded Metrics or X-Ray)
        log_with_correlation_id(self.correlation_id, "Invoking Lambda handler 'hello'")

        try:
            response: Dict[str, Any] = hello(event, context)
            self.assertIsInstance(response, dict, "Handler did not return a dict response")

            status_code = response.get('statusCode')
            body = response.get('body')

            self.assertEqual(status_code, 200, f"Expected statusCode 200, got {status_code}")
            self.assertIsInstance(body, str, f"Expected body as str, got {type(body)}")

            log_with_correlation_id(self.correlation_id, f"Test passed. statusCode={status_code}, body type={type(body).__name__}")
        except Exception as exc:
            log_with_correlation_id(self.correlation_id, f"Exception occurred: {exc}", logging.ERROR)
            # Optionally: insert custom resource cleanup here if necessary
            self.fail(f"Exception raised during handler invocation: {exc}")
>>>>>>> Stashed changes
