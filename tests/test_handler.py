import unittest
import logging
import uuid
from typing import Any, Dict
from handler import hello

# Configure structured logging
logger = logging.getLogger("handler_test")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time":"%(asctime)s", "level":"%(levelname)s", "correlation_id":"%(correlation_id)s", "message":"%(message)s"}'
)
handler.setFormatter(formatter)
logger.handlers = [handler]

def log_with_correlation(correlation_id: str, message: str, level: str = "info") -> None:
    extra = {'correlation_id': correlation_id}
    if level == "info":
        logger.info(message, extra=extra)
    elif level == "error":
        logger.error(message, extra=extra)
    elif level == "warning":
        logger.warning(message, extra=extra)
    else:
        logger.debug(message, extra=extra)

class HandlerTest(unittest.TestCase):

    def setUp(self) -> None:
        self.correlation_id = str(uuid.uuid4())

    def test_event_failsWithNumberAsEvent(self) -> None:
        event = 1
        context = 2

        # Input validation and observability
        try:
            if not isinstance(event, (dict, int, str)):
                raise ValueError(f"Invalid event type: {type(event)}")
            if not isinstance(self.correlation_id, str) or not self.correlation_id:
                raise ValueError("Invalid correlation_id")
            log_with_correlation(
                self.correlation_id,
                f"Testing hello() with event={event!r} and context={context!r}"
            )

            # Simulated metrics (real metrics would use AWS embedded metrics)
            # e.g. EMF or CloudWatch Logs Insights

            response: Dict[str, Any] = hello(event, context)

            self.assertIsInstance(response, dict, msg=f"Response should be a dict, got {type(response)}")
            self.assertEqual(response.get('statusCode'), 200,
                msg=f"Expected statusCode 200, got {response.get('statusCode')}")
            self.assertTrue(isinstance(response.get('body'), str),
                msg="Response body should be a string")

        except Exception as ex:
            log_with_correlation(
                self.correlation_id,
                f"Exception during test_event_failsWithNumberAsEvent: {ex!r}",
                level="error"
            )
            self.fail(f"Exception was raised during test: {ex!r}")
        finally:
            # Resource management: if external connections were opened, close here
            log_with_correlation(
                self.correlation_id,
                "Completed test_event_failsWithNumberAsEvent"
            )