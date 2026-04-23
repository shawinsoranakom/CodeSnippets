def log_message(
    logger,
    message,
    *args,
    level=None,
    status_code=None,
    request=None,
    exception=None,
    **extra,
):
    """Log `message` using `logger` based on `status_code` and logger `level`.

    Pass `request`, `status_code` (if defined) and any provided `extra` as such
    to the logging method,

    Arguments from `args` will be escaped to avoid potential log injections.

    """
    extra = {"request": request, **extra}
    if status_code is not None:
        extra["status_code"] = status_code
        if level is None:
            if status_code >= 500:
                level = "error"
            elif status_code >= 400:
                level = "warning"

    escaped_args = tuple(
        a.encode("unicode_escape").decode("ascii") if isinstance(a, str) else a
        for a in args
    )

    getattr(logger, level or "info")(
        message,
        *escaped_args,
        extra=extra,
        exc_info=exception,
    )