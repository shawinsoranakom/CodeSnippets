def normalize_output(value, ItemType: type):
        if hasattr(ItemType, "_create_with_serializer"):
            value = api.deserialize(value)
            assert isinstance(
                value, pw.PyObjectWrapper
            ), f"expecting PyObjectWrapper, got {type(value)}"
            return value.value

        actual_type = get_args(ItemType) or (ItemType,)
        if pw.Json in actual_type and isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass  # plain string is a valid JSON string value
        # JSON-parse string values for list/tuple types (e.g. MSSQL stores them as JSON strings)
        if isinstance(value, str) and get_origin(ItemType) in (list, tuple):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
        # Parse ndarray JSON representation {"shape":[...],"elements":[...]} back to nested lists
        if isinstance(value, str) and get_origin(ItemType) is np.ndarray:
            try:
                parsed = json.loads(value)
                if (
                    isinstance(parsed, dict)
                    and "shape" in parsed
                    and "elements" in parsed
                ):
                    arr = np.array(parsed["elements"]).reshape(parsed["shape"])
                    return arr.tolist()
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        if hasattr(value, "__iter__") and not isinstance(value, (str, bytes, dict)):
            args = get_args(ItemType)
            nested_arg = None
            for arg in args:
                if arg is not None:
                    nested_arg = arg
                    break
            return [normalize_output(v, nested_arg) for v in value]  # type: ignore
        return value