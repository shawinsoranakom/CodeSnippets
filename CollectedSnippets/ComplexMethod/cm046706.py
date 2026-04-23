def format_error_message(error: Exception, model_name: str) -> str:
    """
    Format user-friendly error messages for common issues.

    Args:
        error: The exception that occurred
        model_name: Name of the model being loaded

    Returns:
        User-friendly error string
    """
    error_str = str(error).lower()
    model_short = model_name.split("/")[-1] if "/" in model_name else model_name

    if "repository not found" in error_str or "404" in error_str:
        return f"Model '{model_short}' not found. Check the model name."

    if "401" in error_str or "unauthorized" in error_str:
        return f"Authentication failed for '{model_short}'. Please provide a valid HF token."

    if "gated" in error_str or "access to model" in error_str:
        return f"Model '{model_short}' requires authentication. Please provide a valid HF token."

    if "invalid user token" in error_str:
        return "Invalid HF token. Please check your token and try again."

    if (
        "memory" in error_str
        or "cuda" in error_str
        or "mlx" in error_str
        or "out of memory" in error_str
    ):
        from utils.hardware import get_device

        device = get_device()
        device_label = {"cuda": "GPU", "mlx": "Apple Silicon GPU", "cpu": "system"}.get(
            device.value, "GPU"
        )
        return f"Not enough {device_label} memory to load '{model_short}'. Try a smaller model or free memory."

    # Generic fallback
    return str(error)