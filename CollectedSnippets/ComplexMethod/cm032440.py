def _failure_text(req) -> str:
    failure = getattr(req, "failure", None)
    if callable(failure):
        try:
            failure = failure()
        except Exception:
            return "unknown"
    if failure is None:
        return "unknown"
    if isinstance(failure, str):
        return failure or "unknown"
    try:
        error_text = getattr(failure, "error_text", None)
        if error_text:
            return str(error_text)
    except Exception:
        pass
    try:
        if isinstance(failure, dict):
            for key in ("errorText", "error_text"):
                value = failure.get(key)
                if value:
                    return str(value)
    except Exception:
        pass
    try:
        getter = getattr(failure, "get", None)
        if callable(getter):
            for key in ("errorText", "error_text"):
                value = getter(key)
                if value:
                    return str(value)
    except Exception:
        pass
    try:
        return str(failure)
    except Exception:
        return "unknown"