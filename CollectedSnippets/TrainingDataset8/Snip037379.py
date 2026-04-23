def _generate_chart(
    chart_type: ChartType,
    data: Data,
    x: Union[str, None] = None,
    y: Union[str, Sequence[str], None] = None,
    width: int = 0,
    height: int = 0,
) -> Chart:
    """This function uses the chart's type, data columns and indices to figure out the chart's spec."""

    if data is None:
        # Use an empty-ish dict because if we use None the x axis labels rotate
        # 90 degrees. No idea why. Need to debug.
        data = {"": []}

    if not isinstance(data, pd.DataFrame):
        data = type_util.convert_anything_to_df(data)

    data, x_column, x_title, y_column, y_title, color_column, color_title = _maybe_melt(
        data, x, y
    )

    opacity = None
    if chart_type == ChartType.AREA and color_column:
        opacity = {y_column: 0.7}
    # Set the X and Y axes' scale to "utc" if they contain date values.
    # This causes time data to be displayed in UTC, rather the user's local
    # time zone. (By default, vega-lite displays time data in the browser's
    # local time zone, regardless of which time zone the data specifies:
    # https://vega.github.io/vega-lite/docs/timeunit.html#output).
    x_scale = (
        alt.Scale(type="utc") if _is_date_column(data, x_column) else alt.Undefined
    )
    y_scale = (
        alt.Scale(type="utc") if _is_date_column(data, y_column) else alt.Undefined
    )

    x_type = alt.Undefined
    # Bar charts should have a discrete (ordinal) x-axis, UNLESS type is date/time
    # https://github.com/streamlit/streamlit/pull/2097#issuecomment-714802475
    if chart_type == ChartType.BAR and not _is_date_column(data, x_column):
        x_type = "ordinal"

    # Use a max tick size of 1 for integer columns (prevents zoom into float numbers)
    # and deactivate grid lines for x-axis
    x_axis_config = alt.Axis(
        tickMinStep=1 if is_integer_dtype(data[x_column]) else alt.Undefined, grid=False
    )
    y_axis_config = alt.Axis(
        tickMinStep=1 if is_integer_dtype(data[y_column]) else alt.Undefined
    )

    tooltips = [
        alt.Tooltip(x_column, title=x_column),
        alt.Tooltip(y_column, title=y_column),
    ]
    color = None

    if color_column:
        color = alt.Color(
            color_column,
            title=color_title,
            type="nominal",
            legend=alt.Legend(titlePadding=0, offset=10, orient="bottom"),
        )
        tooltips.append(alt.Tooltip(color_column, title="label"))

    chart = getattr(
        alt.Chart(data, width=width, height=height),
        "mark_" + chart_type.value,
    )().encode(
        x=alt.X(
            x_column,
            title=x_title,
            scale=x_scale,
            type=x_type,
            axis=x_axis_config,
        ),
        y=alt.Y(y_column, title=y_title, scale=y_scale, axis=y_axis_config),
        tooltip=tooltips,
    )

    if color:
        chart = chart.encode(color=color)

    if opacity:
        chart = chart.encode(opacity=opacity)

    return chart.interactive()