def _sanitize_tune_value(value: dict):
    """Convert NumPy-backed Tune values into native Python types for YAML serialization.

    Args:
        value (dict): The value to convert. Can be a dict, list, tuple, NumPy scalar, or NumPy array.

    Returns:
        The converted value with NumPy types replaced by native Python types.
    """
    if isinstance(value, dict):
        return {k: _sanitize_tune_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_tune_value(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_tune_value(v) for v in value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value