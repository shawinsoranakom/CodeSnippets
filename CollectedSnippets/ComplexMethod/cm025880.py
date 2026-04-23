def stringify_onvif_error(error: Exception) -> str:
    """Stringify ONVIF error."""
    if isinstance(error, Fault):
        message = error.message
        if error.detail is not None:  # checking true is deprecated
            # Detail may be a bytes object, so we need to convert it to string
            if isinstance(error.detail, bytes):
                detail = error.detail.decode("utf-8", "replace")
            else:
                detail = str(error.detail)
            message += ": " + detail
        if error.code is not None:  # checking true is deprecated
            message += f" (code:{error.code})"
        if error.subcodes is not None:  # checking true is deprecated
            message += (
                f" (subcodes:{','.join(extract_subcodes_as_strings(error.subcodes))})"
            )
        if error.actor:
            message += f" (actor:{error.actor})"
    else:
        message = str(error)
    return message or f"Device sent empty error with type {type(error)}"