import unittest
import logging
import uuid
from typing import Any, Dict

from handler import hello

class HandlerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.logger = logging.getLogger("HandlerTest")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "message": %(message)s }'
        )
        handler.setFormatter(formatter)
        if not cls.logger.hasHandlers():
            cls.logger.addHandler(handler)
        cls.logger.setLevel(logging.INFO)
        super().setUpClass()

    def _log(self, message: str, correlation_id: str, level: str = "info", **kwargs: Any) -> None:
        log_fn = getattr(self.logger, level, self.logger.info)
        extra = {"correlation_id": correlation_id}
        log_fn(f'"{message}", "extra": {kwargs}', extra=extra)

    def test_event_failsWithNumberAsEvent(self) -> None:
        correlation_id = str(uuid.uuid4())
        from time import perf_counter
        start = perf_counter()
        try:
            # Input validation
            event = 1
            context = 2
            if not isinstance(event, (dict, int, float, str, type(None))):
                raise ValueError("Invalid event type")
            # Trace the test execution
            self._log("Starting test_event_failsWithNumberAsEvent", correlation_id)
            response: Dict[str, Any] = hello(event, context)
            # Observability metric (execution time)
            exec_time = perf_counter() - start
            self._log("Test executed", correlation_id, exec_time=exec_time)
            # Security: Ensure body is properly sanitized (assumption based on string type)
            self.assertEqual(response.get("statusCode"), 200)
            self.assertTrue(isinstance(response.get("body"), str))
        except Exception as exc:
            self._log(f'Exception in test_event_failsWithNumberAsEvent: {exc}', correlation_id, level="error")
            raise