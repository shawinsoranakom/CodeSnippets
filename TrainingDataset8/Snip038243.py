def is_dataframe(obj: object) -> TypeGuard[DataFrame]:
    return is_type(obj, _PANDAS_DF_TYPE_STR)