import unittest
import logging
import uuid
import time
from typing import Any, Dict

from handler import hello

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler_stream = logging.StreamHandler()
formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "message": "%(message)s"}'
)
handler_stream.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler_stream)

class ContextFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'N/A'
        return True
logger.addFilter(ContextFilter())

def generate_correlation_id() -> str:
    return str(uuid.uuid4())

def validate_event(event: Any) -> bool:
    # Accept only dict or JSONy payloads, sanitize basic numbers
    if not isinstance(event, (dict, str)):
        return False
    return True

class HandlerTest(unittest.TestCase):

    def setUp(self) -> None:
        self.correlation_id = generate_correlation_id()
        self.start_time = time.time()

    def tearDown(self) -> None:
        duration = time.time() - self.start_time
        logger.info(
            f'Test duration: {duration:.4f}s',
            extra={'correlation_id': self.correlation_id}
        )

    def test_event_failsWithNumberAsEvent(self) -> None:
        try:
            event = 1
            context = 2  # Not a real Lambda context, but for compatibility
            if not validate_event(event):
                logger.warning(
                    f'Invalid event type: {type(event)}',
                    extra={'correlation_id': self.correlation_id}
                )
                self.fail(f'Invalid event type: {type(event)}')

            logger.info(
                f'Test started: test_event_failsWithNumberAsEvent',
                extra={'correlation_id': self.correlation_id}
            )

            response: Dict[str, Any] = hello(event, context)  # Assume handler.hello follows Lambda signature

            # Observability: Simple metric
            logger.info(
                f'Response received: statusCode={response.get("statusCode")}',
                extra={'correlation_id': self.correlation_id}
            )

            self.assertEqual(response.get('statusCode'), 200)
            self.assertIsInstance(response.get('body'), str)

        except Exception as exc:
            logger.error(
                f'Exception thrown: {exc!r}',
                extra={'correlation_id': self.correlation_id}
            )
            self.fail(f'Handler threw exception: {exc!r}')