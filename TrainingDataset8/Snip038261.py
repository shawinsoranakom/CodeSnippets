def is_pandas_styler(obj: object) -> TypeGuard[Styler]:
    return is_type(obj, _PANDAS_STYLER_TYPE_STR)