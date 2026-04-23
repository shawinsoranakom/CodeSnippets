def _serialize_dispatcher(obj: Any, max_length: int | None, max_items: int | None) -> Any | _UnserializableSentinel:
    """Dispatch object to appropriate serializer."""
    # Handle primitive types first
    if obj is None:
        return obj
    primitive = _serialize_primitive(obj, max_length, max_items)
    if primitive is not UNSERIALIZABLE_SENTINEL:
        return primitive

    match obj:
        case str():
            return _serialize_str(obj, max_length, max_items)
        case bytes():
            return _serialize_bytes(obj, max_length, max_items)
        case datetime():
            return _serialize_datetime(obj, max_length, max_items)
        case Decimal():
            return _serialize_decimal(obj, max_length, max_items)
        case UUID():
            return _serialize_uuid(obj, max_length, max_items)
        case Document():
            return _serialize_document(obj, max_length, max_items)
        case AsyncIterator() | Generator() | Iterator():
            return _serialize_iterator(obj, max_length, max_items)
        case BaseModel():
            return _serialize_pydantic(obj, max_length, max_items)
        case BaseModelV1():
            return _serialize_pydantic_v1(obj, max_length, max_items)
        case dict():
            return _serialize_dict(obj, max_length, max_items)
        case pd.DataFrame():
            return _serialize_dataframe(obj, max_length, max_items)
        case pd.Series():
            return _serialize_series(obj, max_length, max_items)
        case list() | tuple():
            return _serialize_list_tuple(obj, max_length, max_items)
        case object() if _is_numpy_type(obj):
            return _serialize_numpy_type(obj, max_length, max_items)
        case object() if not isinstance(obj, type):  # Match any instance that's not a class
            return _serialize_instance(obj, max_length, max_items)
        case object() if hasattr(obj, "_name_"):  # Enum case
            return f"{obj.__class__.__name__}.{obj._name_}"
        case object() if hasattr(obj, "__name__") and hasattr(obj, "__bound__"):  # TypeVar case
            return repr(obj)
        case object() if hasattr(obj, "__origin__") or hasattr(obj, "__parameters__"):  # Type alias/generic case
            return repr(obj)
        case _:
            # Handle numpy numeric types (int, float, bool, complex)
            if hasattr(obj, "dtype"):
                if np.issubdtype(obj.dtype, np.number) and hasattr(obj, "item"):
                    return obj.item()
                if np.issubdtype(obj.dtype, np.bool_):
                    return bool(obj)
                if np.issubdtype(obj.dtype, np.complexfloating):
                    return complex(cast("complex", obj))
                if np.issubdtype(obj.dtype, np.str_):
                    return str(obj)
                if np.issubdtype(obj.dtype, np.bytes_) and hasattr(obj, "tobytes"):
                    return obj.tobytes().decode("utf-8", errors="ignore")
                if np.issubdtype(obj.dtype, np.object_) and hasattr(obj, "item"):
                    return serialize(obj.item())
            return UNSERIALIZABLE_SENTINEL