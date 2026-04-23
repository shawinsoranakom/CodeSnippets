def serialize(
    obj: Any,
    max_length: int | None = None,
    max_items: int | None = None,
    *,
    to_str: bool = False,
) -> Any:
    """Unified serialization with optional truncation support.

    Coordinates specialized serializers through a dispatcher pattern.
    Maintains recursive processing for nested structures.

    Args:
        obj: Object to serialize
        max_length: Maximum length for string values, None for no truncation
        max_items: Maximum items in list-like structures, None for no truncation
        to_str: If True, return a string representation of the object if serialization fails
    """
    if obj is None:
        return None
    try:
        # First try type-specific serialization
        result = _serialize_dispatcher(obj, max_length, max_items)
        if result is not UNSERIALIZABLE_SENTINEL:  # Special check for None since it's a valid result
            return result

        # Handle class-based Pydantic types and other types
        if isinstance(obj, type):
            if issubclass(obj, BaseModel | BaseModelV1):
                return repr(obj)
            return str(obj)  # Handle other class types

        # Handle type aliases and generic types
        if hasattr(obj, "__origin__") or hasattr(obj, "__parameters__"):  # Type alias or generic type check
            try:
                return repr(obj)
            except Exception:  # noqa: BLE001
                logger.debug(f"Error serializing object: {obj}", exc_info=True)

        # Fallback to common serialization patterns
        if hasattr(obj, "model_dump"):
            return serialize(obj.model_dump(), max_length, max_items)
        if hasattr(obj, "dict") and not isinstance(obj, type):
            return serialize(obj.dict(), max_length, max_items)

        # Final fallback to string conversion only if explicitly requested
        if to_str:
            return str(obj)

    except Exception:  # noqa: BLE001
        return "[Unserializable Object]"
    return obj