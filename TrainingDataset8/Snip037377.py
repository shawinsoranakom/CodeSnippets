def _melt_data(
    data_df: pd.DataFrame,
    x_column: str,
    y_column: str,
    color_column: str,
    value_columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Converts a wide-format dataframe to a long-format dataframe."""

    data_df = pd.melt(
        data_df,
        id_vars=[x_column],
        value_vars=value_columns,
        var_name=color_column,
        value_name=y_column,
    )

    y_series = data_df[y_column]
    if (
        y_series.dtype == "object"
        and "mixed" in infer_dtype(y_series)
        and len(y_series.unique()) > 100
    ):
        raise StreamlitAPIException(
            "The columns used for rendering the chart contain too many values with mixed types. Please select the columns manually via the y parameter."
        )

    # Arrow has problems with object types after melting two different dtypes
    # pyarrow.lib.ArrowTypeError: "Expected a <TYPE> object, got a object"
    data_df = type_util.fix_arrow_incompatible_column_types(
        data_df, selected_columns=[x_column, color_column, y_column]
    )

    return data_df