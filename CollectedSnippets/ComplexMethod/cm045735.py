def _get_expected_python_type(ItemType: type) -> type | tuple:
    import types as builtin_types

    origin = get_origin(ItemType)

    if origin is Union or (
        hasattr(builtin_types, "UnionType") and origin is builtin_types.UnionType
    ):
        args = get_args(ItemType)
        non_none_args = [a for a in args if a is not type(None)]
        inner = _get_expected_python_type(non_none_args[0])
        if isinstance(inner, tuple):
            return inner + (type(None),)
        return (inner, type(None))

    if origin is not None:
        return origin

    if ItemType is pw.Duration:
        return pd.Timedelta
    if ItemType in (pw.DateTimeNaive, pw.DateTimeUtc):
        return pd.Timestamp

    return ItemType