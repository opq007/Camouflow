"""Logging helpers (no Qt dependency after HTML refactor)."""

from __future__ import annotations

import logging


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s [%(profile)s]: %(message)s"


class ProfileFormatter(logging.Formatter):
    """Formatter that tolerates third-party records without profile context."""

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "profile") or record.profile in (None, ""):
            record.profile = "-"
        return super().format(record)


class ProfileContextFilter(logging.Filter):
    """Ensure every log record has a profile attribute for formatting."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "profile") or record.profile in (None, ""):
            record.profile = "-"
        return True


PROFILE_FILTER = ProfileContextFilter()


def install_profile_log_record_factory() -> None:
    """Backward-compatible no-op; ProfileFormatter handles missing profile."""
    return