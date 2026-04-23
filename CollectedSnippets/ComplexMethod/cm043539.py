def remove_timezone_from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Remove timezone information from a dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        The dataframe to remove timezone information from

    Returns
    -------
    pd.DataFrame
        The dataframe with timezone information removed
    """
    date_cols = []
    index_is_date = False

    # Find columns and index containing date data
    if (
        df.index.dtype.kind == "M"
        and hasattr(df.index.dtype, "tz")
        and df.index.dtype.tz is not None  # type: ignore
    ):
        index_is_date = True

    for col, dtype in df.dtypes.items():
        if dtype.kind == "M" and hasattr(df.index.dtype, "tz") and dtype.tz is not None:
            date_cols.append(col)

    # Remove the timezone information
    for col in date_cols:
        df[col] = df[col].dt.date

    if index_is_date:
        index_name = df.index.name
        df.index = df.index.date  # type: ignore
        df.index.name = index_name

    return df