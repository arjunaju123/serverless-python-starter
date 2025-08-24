import unittest
import logging
import uuid
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Any, Dict
from handler import hello

# Setup structured and performant logging
logger = logging.getLogger("HandlerTest")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time":"%(asctime)s", "level":"%(levelname)s", "message":"%(message)s", "correlation_id":"%(correlation_id)s"}'
)
handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(handler)

def with_correlation_id(extra: Dict[str, Any] = None) -> Dict[str, Any]:
    correlation_id = str(uuid.uuid4())
    return {"correlation_id": correlation_id, **(extra or {})}

def sanitize_event(event: Any) -> Any:
    # Basic input sanitization and validation for security
    # Here we just check type for demonstration; expand as needed
    if not isinstance(event, (dict, str, int, float)):  # Allow only certain input types
        raise ValueError("Invalid event type")
    return event

class HandlerTest(unittest.TestCase):

    def setUp(self) -> None:
        self.correlation_context = with_correlation_id()
        self.dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        logger.info(
            "Test setup completed",
            extra=self.correlation_context,
        )

    def tearDown(self) -> None:
        # Clean up resources if necessary (close Boto3 resources if applicable)
        # Boto3 doesn't require explicit close, but include any cleanups here
        logger.info(
            "Test teardown completed",
            extra=self.correlation_context,
        )

    def test_event_failsWithNumberAsEvent(self) -> None:
        event = 1
        context = 2

        # Add observability: beginning of test
        logger.info(
            f"Running test_event_failsWithNumberAsEvent with event={event}, context={context}",
            extra=self.correlation_context,
        )

        response = None
        try:
            # Input sanitization
            sanitized_event = sanitize_event(event)
            sanitized_context = sanitize_event(context)

            # Lambda patterns: pass event and context as would AWS Lambda
            response = hello(sanitized_event, sanitized_context)

            # Observability: log response, pseudo-metric
            logger.info(
                f"Handler response status: {response.get('statusCode')}",
                extra=self.correlation_context,
            )
            # Dummy custom metric (replace with real metrics/tracing as needed)
            logger.info(
                "Metric:TestInvocations=1",
                extra=self.correlation_context,
            )
        except (ClientError, BotoCoreError) as aws_err:
            logger.error(
                f"AWS SDK error occurred: {aws_err}",
                extra=self.correlation_context,
            )
            self.fail(f"Test failed due to AWS SDK error: {aws_err}")
        except ValueError as val_err:
            logger.warning(
                f"Input validation failed: {val_err}",
                extra=self.correlation_context,
            )
            self.fail(f"Test failed with input validation error: {val_err}")
        except Exception as exc:
            logger.error(
                f"Unhandled exception in test: {exc}",
                extra=self.correlation_context,
            )
            self.fail(f"Test failed with unhandled exception: {exc}")

        self.assertIsNotNone(response)
        self.assertEqual(response.get("statusCode"), 200)
        self.assertIsInstance(response.get("body"), str)