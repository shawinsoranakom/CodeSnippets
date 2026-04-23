def is_retryable_server_bind_error(
    exc: Exception | None,
    output: str = "",
    *,
    exited_quickly: bool = False,
) -> bool:
    haystack = output.lower()
    bind_markers = (
        "address already in use",
        "only one usage of each socket address",
        "failed to bind",
        "bind failed",
        "failed to listen",
        "errno 98",
        "errno 10048",
    )
    if any(marker in haystack for marker in bind_markers):
        return True

    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if exited_quickly and isinstance(reason, ConnectionRefusedError):
            return True
        if isinstance(reason, OSError) and reason.errno in {
            98,
            99,
            111,
            10048,
            10049,
            10061,
        }:
            return exited_quickly
    if exited_quickly and isinstance(exc, ConnectionRefusedError):
        return True
    if isinstance(exc, OSError) and exc.errno in {98, 99, 111, 10048, 10049, 10061}:
        return exited_quickly
    return False