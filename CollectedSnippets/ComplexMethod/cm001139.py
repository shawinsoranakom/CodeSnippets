def _before_send(event, hint):
    """Filter out expected/transient errors from Sentry to reduce noise."""
    if "exc_info" in hint:
        exc_type, exc_value, _ = hint["exc_info"]
        exc_msg = str(exc_value).lower() if exc_value else ""

        # AMQP/RabbitMQ transient connection errors — expected during deploys
        if any(kw in exc_msg for kw in _AMQP_KEYWORDS):
            return None

        # "connection refused" only for AMQP-related exceptions (not other services)
        if "connection refused" in exc_msg:
            exc_module = getattr(exc_type, "__module__", "") or ""
            exc_name = getattr(exc_type, "__name__", "") or ""
            if any(
                ind in exc_module.lower() or ind in exc_name.lower()
                for ind in _AMQP_INDICATORS
            ) or any(kw in exc_msg for kw in _AMQP_INDICATORS):
                return None

        # User-caused credential/auth/integration errors — not platform bugs
        if any(kw in exc_msg for kw in _USER_AUTH_KEYWORDS):
            return None

        # Expected business logic — insufficient balance
        if "insufficient balance" in exc_msg or "no credits left" in exc_msg:
            return None

        # Expected security check — blocked IP access
        if "access to blocked or private ip" in exc_msg:
            return None

        # Discord bot token misconfiguration — not a platform error
        if "improper token has been passed" in exc_msg or (
            exc_type and exc_type.__name__ == "Forbidden" and "50001" in exc_msg
        ):
            return None

        # Prisma UniqueViolationError — always caught and handled in our codebase.
        # These arise from concurrent create operations racing on unique constraints
        # (workspace files, credits, library folders, store listings, chat messages).
        # Every call site has an except handler; the global FastAPI handler also
        # catches them and returns 400.  Safe to drop unconditionally.
        if exc_type and exc_type.__name__ == "UniqueViolationError":
            return None

        # Google metadata DNS errors — expected in non-GCP environments
        if (
            "metadata.google.internal" in exc_msg
            and settings.config.behave_as != BehaveAs.CLOUD
        ):
            return None

        # Inactive email recipients — expected for bounced addresses
        if "marked as inactive" in exc_msg or "inactive addresses" in exc_msg:
            return None

    # Also filter log-based events for known noisy messages.
    # Sentry's LoggingIntegration stores log messages under "logentry", not "message".
    logentry = event.get("logentry") or {}
    log_msg = (
        logentry.get("formatted") or logentry.get("message") or event.get("message")
    )
    if event.get("logger") and log_msg:
        msg = log_msg.lower()
        noisy_log_patterns = [
            "amqpconnection",
            "connection_forced",
            "unclosed client session",
            "unclosed connector",
        ]
        if any(p in msg for p in noisy_log_patterns):
            return None
        if "connection refused" in msg and any(ind in msg for ind in _AMQP_INDICATORS):
            return None
        # Same auth keywords — errors logged via logger.error() bypass exc_info
        if any(kw in msg for kw in _USER_AUTH_KEYWORDS):
            return None

    return event