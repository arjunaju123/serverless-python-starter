import unittest
import logging
import uuid
from typing import Any, Dict

from handler import hello

# Configure structured logging for Lambda best practices
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class HandlerTest(unittest.TestCase):
    def setUp(self) -> None:
        # Generate a unique correlation ID for each test
        self.correlation_id = str(uuid.uuid4())
        logger.info(f"Test setup started", extra={"correlation_id": self.correlation_id})

    def tearDown(self) -> None:
        logger.info("Test teardown complete", extra={"correlation_id": self.correlation_id})

    def _log_exception(self, e: Exception) -> None:
        logger.error(
            f"Exception occurred: {str(e)}",
            exc_info=True,
            extra={"correlation_id": self.correlation_id}
        )

    def _validate_response(self, response: Dict[str, Any]) -> bool:
        if not isinstance(response, dict):
            logger.error(
                "Response is not a dictionary as expected",
                extra={"correlation_id": self.correlation_id}
            )
            return False
        if "statusCode" not in response or "body" not in response:
            logger.error(
                "Response missing required keys",
                extra={"correlation_id": self.correlation_id}
            )
            return False
        return True

    def test_event_failsWithNumberAsEvent(self) -> None:
        # Sample test metric
        logger.info(
            "Running test_event_failsWithNumberAsEvent",
            extra={"correlation_id": self.correlation_id, "metric": "HandlerTest.Invocations", "metric_value": 1}
        )
        try:
            # Input validation and sanitization
            event, context = 1, 2
            if not isinstance(event, (dict, str, int, float)):
                raise ValueError("Invalid event type for Lambda handler")
            
            response = hello(event, context)
            self.assertTrue(self._validate_response(response))

            status_code = response.get('statusCode')
            body = response.get('body')

            self.assertEqual(status_code, 200, f"Expected 200 statusCode but got {status_code}")
            self.assertIsInstance(body, str, "Body should be of type str")
            logger.info(
                "Test test_event_failsWithNumberAsEvent passed",
                extra={"correlation_id": self.correlation_id}
            )
        except Exception as e:
            self._log_exception(e)
            self.fail(f"Unexpected exception during test: {e}")