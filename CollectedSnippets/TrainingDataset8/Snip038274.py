def data_frame_to_bytes(df: DataFrame) -> bytes:
    """Serialize pandas.DataFrame to bytes using Apache Arrow.

    Parameters
    ----------
    df : pandas.DataFrame
        A dataframe to convert.

    """
    try:
        table = pa.Table.from_pandas(df)
    except (pa.ArrowTypeError, pa.ArrowInvalid, pa.ArrowNotImplementedError):
        _LOGGER.info(
            "Applying automatic fixes for column types to make the dataframe Arrow-compatible."
        )
        df = fix_arrow_incompatible_column_types(df)
        table = pa.Table.from_pandas(df)
    return pyarrow_table_to_bytes(table)