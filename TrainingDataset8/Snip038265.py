def convert_anything_to_df(
    df: Any, max_unevaluated_rows: int = MAX_UNEVALUATED_DF_ROWS
) -> DataFrame:
    """Try to convert different formats to a Pandas Dataframe.

    Parameters
    ----------
    df : ndarray, Iterable, dict, DataFrame, Styler, pa.Table, None, dict, list, or any

    max_unevaluated_rows: int
        If unevaluated data is detected this func will evaluate it,
        taking max_unevaluated_rows, defaults to 10k and 100 for st.table

    Returns
    -------
    pandas.DataFrame

    """
    # This is inefficient as the data will be converted back to Arrow
    # when marshalled to protobuf, but area/bar/line charts need
    # DataFrame magic to generate the correct output.
    if isinstance(df, pa.Table):
        return df.to_pandas()

    if is_type(df, _PANDAS_DF_TYPE_STR):
        return df

    if is_pandas_styler(df):
        return df.data

    import pandas as pd

    if is_type(df, "numpy.ndarray") and len(df.shape) == 0:
        return pd.DataFrame([])

    if (
        is_type(df, _SNOWPARK_DF_TYPE_STR)
        or is_type(df, _SNOWPARK_TABLE_TYPE_STR)
        or is_type(df, _PYSPARK_DF_TYPE_STR)
    ):
        if is_type(df, _PYSPARK_DF_TYPE_STR):
            df = df.limit(max_unevaluated_rows).toPandas()
        else:
            df = pd.DataFrame(df.take(max_unevaluated_rows))
        if df.shape[0] == max_unevaluated_rows:
            st.caption(
                f"⚠️ Showing only {string_util.simplify_number(max_unevaluated_rows)} rows. "
                "Call `collect()` on the dataframe to show more."
            )
        return df

    # Try to convert to pandas.DataFrame. This will raise an error is df is not
    # compatible with the pandas.DataFrame constructor.
    try:
        return pd.DataFrame(df)

    except ValueError:
        raise errors.StreamlitAPIException(
            """
Unable to convert object of type `%(type)s` to `pandas.DataFrame`.

Offending object:
```py
%(object)s
```"""
            % {
                "type": type(df),
                "object": df,
            }
        )