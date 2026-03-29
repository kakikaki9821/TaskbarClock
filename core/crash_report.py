"""Sentry crash reporting initialization."""

from loguru import logger

SENTRY_DSN = ""  # Set your Sentry DSN here or via environment variable


def setup_sentry() -> None:
    """Initialize Sentry SDK for crash reporting."""
    import os

    dsn = os.environ.get("TASKBAR_CLOCK_SENTRY_DSN", SENTRY_DSN)
    if not dsn:
        logger.info("Sentry DSN not configured, crash reporting disabled")
        return

    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=0.0,
            send_default_pii=False,
            environment="production",
        )
        logger.info("Sentry initialized")
    except Exception as e:
        logger.warning("Failed to initialize Sentry: {}", e)
