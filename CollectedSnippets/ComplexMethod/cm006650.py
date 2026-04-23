def _serialize_numpy_type(obj: Any, max_length: int | None, max_items: int | None) -> Any:
    """Serialize numpy types."""
    try:
        # For single-element arrays
        if obj.size == 1 and hasattr(obj, "item"):
            return obj.item()

        # For multi-element arrays
        if np.issubdtype(obj.dtype, np.number):
            return obj.tolist()  # Convert to Python list
        if np.issubdtype(obj.dtype, np.bool_):
            return bool(obj)
        if np.issubdtype(obj.dtype, np.complexfloating):
            return complex(cast("complex", obj))
        if np.issubdtype(obj.dtype, np.str_):
            return _serialize_str(str(obj), max_length, max_items)
        if np.issubdtype(obj.dtype, np.bytes_) and hasattr(obj, "tobytes"):
            return _serialize_bytes(obj.tobytes(), max_length, max_items)
        if np.issubdtype(obj.dtype, np.object_) and hasattr(obj, "item"):
            return _serialize_instance(obj.item(), max_length, max_items)
    except Exception:  # noqa: BLE001
        return UNSERIALIZABLE_SENTINEL
    return UNSERIALIZABLE_SENTINEL