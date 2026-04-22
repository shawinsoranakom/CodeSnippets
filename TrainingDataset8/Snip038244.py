def is_dataframe_like(obj: object) -> TypeGuard[DataFrameLike]:
    return any(is_type(obj, t) for t in _DATAFRAME_LIKE_TYPES)