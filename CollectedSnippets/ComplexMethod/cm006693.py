def _format_plain_reason(exception: BaseException) -> str:
        """Format the error reason without markdown."""
        if hasattr(exception, "body") and isinstance(exception.body, dict) and "message" in exception.body:
            reason = f"{exception.body.get('message')}\n"
        elif hasattr(exception, "_message"):
            reason = f"{exception._message()}\n" if callable(exception._message) else f"{exception._message}\n"  # noqa: SLF001
        elif hasattr(exception, "code"):
            reason = f"Code: {exception.code}\n"
        elif hasattr(exception, "args") and exception.args:
            reason = f"{exception.args[0]}\n"
        elif isinstance(exception, ValidationError):
            reason = f"{exception!s}\n"
        elif hasattr(exception, "detail"):
            reason = f"{exception.detail}\n"
        elif hasattr(exception, "message"):
            reason = f"{exception.message}\n"
        else:
            reason = "An unknown error occurred.\n"
        return reason