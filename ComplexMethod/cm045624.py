def _validate_dataframe(df: pd.DataFrame, stacklevel: int = 1) -> None:
    for pseudocolumn in api.PANDAS_PSEUDOCOLUMNS:
        if pseudocolumn in df.columns:
            if not pd.api.types.is_integer_dtype(df[pseudocolumn].dtype):
                raise ValueError(f"Column {pseudocolumn} has to contain integers only.")
    if api.TIME_PSEUDOCOLUMN in df.columns:
        if any(df[api.TIME_PSEUDOCOLUMN] < 0):
            raise ValueError(
                f"Column {api.TIME_PSEUDOCOLUMN} cannot contain negative times."
            )
        if any(df[api.TIME_PSEUDOCOLUMN] % 2 == 1):
            warn(
                "timestamps are required to be even; all timestamps will be doubled",
                stacklevel=stacklevel + 1,
            )
            df[api.TIME_PSEUDOCOLUMN] = 2 * df[api.TIME_PSEUDOCOLUMN]

    if api.DIFF_PSEUDOCOLUMN in df.columns:
        if any((df[api.DIFF_PSEUDOCOLUMN] != 1) & (df[api.DIFF_PSEUDOCOLUMN] != -1)):
            raise ValueError(
                f"Column {api.DIFF_PSEUDOCOLUMN} can only have 1 and -1 values."
            )