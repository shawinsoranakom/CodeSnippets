def _is_field_useful(inst: Serializable, key: str, value: Any) -> bool:
    """Check if a field is useful as a constructor argument.

    Args:
        inst: The instance.
        key: The key.
        value: The value.

    Returns:
        Whether the field is useful. If the field is required, it is useful.
        If the field is not required, it is useful if the value is not `None`.
        If the field is not required and the value is `None`, it is useful if the
        default value is different from the value.
    """
    field = type(inst).model_fields.get(key)
    if not field:
        return False

    if field.is_required():
        return True

    # Handle edge case: a value cannot be converted to a boolean (e.g. a
    # Pandas DataFrame).
    try:
        value_is_truthy = bool(value)
    except Exception as _:
        value_is_truthy = False

    if value_is_truthy:
        return True

    # Value is still falsy here!
    if field.default_factory is dict and isinstance(value, dict):
        return False

    # Value is still falsy here!
    if field.default_factory is list and isinstance(value, list):
        return False

    value_neq_default = _try_neq_default(value, field)

    # If value is falsy and does not match the default
    return value_is_truthy or value_neq_default