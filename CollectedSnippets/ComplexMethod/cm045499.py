def extract_real_error(e: Exception) -> str:
    """Extract the real error message from potentially wrapped exceptions"""
    error_parts: List[str] = []

    # Handle ExceptionGroup (Python 3.11+)
    if hasattr(e, "exceptions") and getattr(e, "exceptions", None):
        exceptions_list = getattr(e, "exceptions", [])
        for sub_exc in exceptions_list:
            error_parts.append(f"{type(sub_exc).__name__}: {str(sub_exc)}")

    # Handle chained exceptions
    elif hasattr(e, "__cause__") and e.__cause__:
        current = e
        while current:
            error_parts.append(f"{type(current).__name__}: {str(current)}")
            current = getattr(current, "__cause__", None)

    # Handle context exceptions
    elif hasattr(e, "__context__") and e.__context__:
        error_parts.append(f"Context: {type(e.__context__).__name__}: {str(e.__context__)}")
        error_parts.append(f"Error: {type(e).__name__}: {str(e)}")

    # Default case
    else:
        error_parts.append(f"{type(e).__name__}: {str(e)}")

    return " | ".join(error_parts)