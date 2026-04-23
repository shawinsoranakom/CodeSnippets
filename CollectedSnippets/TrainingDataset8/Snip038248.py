def is_dataframe_compatible(obj: object) -> TypeGuard[DataFrameCompatible]:
    """True if type that can be passed to convert_anything_to_df."""
    return is_dataframe_like(obj) or type(obj) in _DATAFRAME_COMPATIBLE_TYPES