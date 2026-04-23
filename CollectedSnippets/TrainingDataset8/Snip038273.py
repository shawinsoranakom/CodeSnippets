def fix_arrow_incompatible_column_types(
    df: DataFrame, selected_columns: Optional[List[str]] = None
) -> DataFrame:
    """Fix column types that are not supported by Arrow table.

    This includes mixed types (e.g. mix of integers and strings)
    as well as complex numbers (complex128 type). These types will cause
    errors during conversion of the dataframe to an Arrow table.
    It is fixed by converting all values of the column to strings
    This is sufficient for displaying the data on the frontend.

    Parameters
    ----------
    df : pandas.DataFrame
        A dataframe to fix.

    selected_columns: Optional[List[str]]
        A list of columns to fix. If None, all columns are evaluated.

    Returns
    -------
    The fixed dataframe.
    """

    for col in selected_columns or df.columns:
        if _is_colum_type_arrow_incompatible(df[col]):
            df[col] = df[col].astype(str)

    # The index can also contain mixed types
    # causing Arrow issues during conversion.
    # Skipping multi-indices since they won't return
    # the correct value from infer_dtype
    if not selected_columns and (
        not isinstance(
            df.index,
            MultiIndex,
        )
        and _is_colum_type_arrow_incompatible(df.index)
    ):
        df.index = df.index.astype(str)
    return df