def _os_error_messages(exc: BaseException) -> list[str]:
    messages: list[str] = []
    if isinstance(exc, OSError):
        for value in (
            getattr(exc, "strerror", None),
            getattr(exc, "filename", None),
            getattr(exc, "filename2", None),
        ):
            if isinstance(value, str) and value:
                messages.append(value)
    text = str(exc)
    if text:
        messages.append(text)
    return [message.lower() for message in messages if message]