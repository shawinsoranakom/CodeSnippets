def _maybe_melt(
    data_df: pd.DataFrame,
    x: Union[str, None] = None,
    y: Union[str, Sequence[str], None] = None,
) -> Tuple[pd.DataFrame, str, str, str, str, Optional[str], Optional[str]]:
    """Determines based on the selected x & y parameter, if the data needs to
    be converted to a long-format dataframe. If so, it returns the melted dataframe
    and the x, y, and color columns used for rendering the chart.
    """

    color_column: Optional[str]
    # This has to contain an empty space, otherwise the
    # full y-axis disappears (maybe a bug in vega-lite)?
    color_title: Optional[str] = " "

    y_column = "value"
    y_title = ""

    if x and isinstance(x, str):
        # x is a single string -> use for x-axis
        x_column = x
        x_title = x
        if x_column not in data_df.columns:
            raise StreamlitAPIException(
                f"{x_column} (x parameter) was not found in the data columns or keys”."
            )
    else:
        # use index for x-axis
        x_column = data_df.index.name or "index"
        x_title = ""
        data_df = data_df.reset_index()

    if y and type_util.is_sequence(y) and len(y) == 1:
        # Sequence is only a single element
        y = str(y[0])

    if y and isinstance(y, str):
        # y is a single string -> use for y-axis
        y_column = y
        y_title = y
        if y_column not in data_df.columns:
            raise StreamlitAPIException(
                f"{y_column} (y parameter) was not found in the data columns or keys”."
            )

        # Set var name to None since it should not be used
        color_column = None
    elif y and type_util.is_sequence(y):
        color_column = "variable"
        # y is a list -> melt dataframe into value vars provided in y
        value_columns: List[str] = []
        for col in y:
            if str(col) not in data_df.columns:
                raise StreamlitAPIException(
                    f"{str(col)} in y parameter was not found in the data columns or keys”."
                )
            value_columns.append(str(col))

        if x_column in [y_column, color_column]:
            raise StreamlitAPIException(
                f"Unable to melt the table. Please rename the columns used for x ({x_column}) or y ({y_column})."
            )

        data_df = _melt_data(data_df, x_column, y_column, color_column, value_columns)
    else:
        color_column = "variable"
        # -> data will be melted into the value prop for y
        data_df = _melt_data(data_df, x_column, y_column, color_column)

    relevant_columns = []
    if x_column and x_column not in relevant_columns:
        relevant_columns.append(x_column)
    if color_column and color_column not in relevant_columns:
        relevant_columns.append(color_column)
    if y_column and y_column not in relevant_columns:
        relevant_columns.append(y_column)
    # Only select the relevant columns required for the chart
    # Other columns can be ignored
    data_df = data_df[relevant_columns]
    return data_df, x_column, x_title, y_column, y_title, color_column, color_title