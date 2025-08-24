import unittest
import logging
import uuid
from typing import Any, Dict

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    boto3 = None

from handler import hello

logger = logging.getLogger("HandlerTest")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


def log_with_correlation_id(message: str, correlation_id: str, level: int = logging.INFO) -> None:
    logger.log(level, message, extra={"correlation_id": correlation_id})


class HandlerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._session = None
        if boto3:
            try:
                cls._session = boto3.session.Session()
                log_with_correlation_id(
                    "Initialized boto3 session for tests.",
                    correlation_id="global"
                )
            except (BotoCoreError, ClientError) as exc:
                log_with_correlation_id(
                    f"Failed to initialize boto3 session: {exc}",
                    correlation_id="global",
                    level=logging.ERROR,
                )
        else:
            log_with_correlation_id(
                "boto3 is not available for import.",
                correlation_id="global",
                level=logging.WARNING,
            )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._session = None
        log_with_correlation_id("Cleaned up boto3 session.", correlation_id="global")

    def test_event_failsWithNumberAsEvent(self) -> None:
        correlation_id = str(uuid.uuid4())
        log_with_correlation_id(
            "Starting test_event_failsWithNumberAsEvent.", correlation_id
        )
        event, context = 1, 2

        # Input validation and sanitization
        if not isinstance(event, (dict, int, str, list)):
            log_with_correlation_id(
                f"Invalid event type: {type(event).__name__}",
                correlation_id,
                level=logging.ERROR,
            )
            self.fail("Input event type is invalid.")

        try:
            response: Dict[str, Any] = hello(event, context)

            # Metric: Synthetic count of handler calls
            log_with_correlation_id(
                "Incrementing test_handler_invocations metric",
                correlation_id
            )

            self.assertIsInstance(response, dict, "Handler response is not a dict.")
            self.assertEqual(response.get("statusCode"), 200, "statusCode is not 200")
            self.assertTrue(
                isinstance(response.get("body"), str), "body is not a string"
            )
        except Exception as e:
            log_with_correlation_id(
                f"Exception during test execution: {e}",
                correlation_id,
                level=logging.ERROR,
            )
            self.fail(f"Test failed with exception: {e}")
        finally:
            # Resource cleanup or extra tracing if necessary
            log_with_correlation_id(
                "Finished test_event_failsWithNumberAsEvent.", correlation_id
            )