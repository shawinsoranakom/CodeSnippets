def bar_increasing_decreasing(  # pylint: disable=W0102
    keys: list[str],
    values: list[int | float],
    title: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    colors: list[str] = ["blue", "red"],
    orientation: Literal["h", "v"] = "h",
    barmode: Literal["group", "stack", "relative", "overlay"] = "relative",
    layout_kwargs: dict[str, Any] | None = None,
) -> Union["OpenBBFigure", "Figure"]:
    """Create a bar chart with increasing and decreasing values represented by two colors.

    Parameters
    ----------
    keys : List[str]
        The x-axis keys.
    values : List[Any]
        The y-axis values.
    title : Optional[str], optional
        The title of the chart, by default None.
    xtitle : Optional[str], optional
        The x-axis title, by default None.
    ytitle : Optional[str], optional
        The y-axis title, by default None.
    colors : List[str], optional
        The colors to use for increasing and decreasing values, by default ["blue", "red"].
    orientation : Literal["h", "v"], optional
        The orientation of the bars, by default "h".
    barmode : Literal["group", "stack", "relative", "overlay"], optional
        The bar mode, by default "relative".
    layout_kwargs : Optional[Dict[str, Any]], optional
        Additional keyword arguments to apply with figure.update_layout(), by default None.

    Returns
    -------
    OpenBBFigure
        The OpenBBFigure object.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_charting.core.openbb_figure import OpenBBFigure  # noqa
    from pandas import Series

    try:
        figure = OpenBBFigure()
    except Exception as _:
        figure = OpenBBFigure(create_backend=True)

    figure = figure.create_subplots(
        1,
        1,
        shared_xaxes=False,
        vertical_spacing=0.06,
        horizontal_spacing=0.01,
        row_width=[1],
        specs=[[{"secondary_y": True}]],
    )

    try:
        data = Series(data=values, index=keys)
        increasing_data = data[data > 0]  # type: ignore
        decreasing_data = data[data < 0]  # type: ignore
    except Exception as e:
        raise ValueError(f"Error: {e}") from e

    if not increasing_data.empty:  # type: ignore
        figure.add_bar(
            x=increasing_data.index if orientation == "v" else increasing_data,  # type: ignore
            y=increasing_data if orientation == "v" else increasing_data.index,  # type: ignore
            marker=dict(color=colors[0]),
            orientation=orientation,
            showlegend=False,
            width=0.95 / len(keys) * 0.75 if barmode == "group" else 0.95,
            hoverinfo="y" if orientation == "v" else "x",
        )
    if not decreasing_data.empty:  # type: ignore
        figure.add_bar(
            x=decreasing_data.index if orientation == "v" else decreasing_data,  # type: ignore
            y=decreasing_data if orientation == "v" else decreasing_data.index,  # type: ignore
            marker=dict(color=colors[1]),
            orientation=orientation,
            showlegend=False,
            width=0.95 / len(keys) * 0.75 if barmode == "group" else 0.95,
            hoverinfo="y" if orientation == "v" else "x",
        )

    figure.update_layout(
        title=dict(text=title if title else None, x=0.5, font=dict(size=20)),
        hovermode="x" if orientation == "v" else "y",
        hoverlabel=dict(align="left" if orientation == "h" else "auto"),
        yaxis=dict(
            title=dict(
                text=ytitle if ytitle else None, standoff=30, font=dict(size=16)
            ),
            side="left" if orientation == "h" else "right",
            showgrid=orientation == "v",
            gridcolor="rgba(128,128,128,0.25)",
            tickfont=dict(size=12),
            ticklen=0,
            categoryorder="array" if orientation == "h" else None,
            categoryarray=keys if orientation == "h" else None,
        ),
        xaxis=dict(
            title=dict(
                text=xtitle if xtitle else None, standoff=30, font=dict(size=16)
            ),
            showgrid=orientation == "h",
            gridcolor="rgba(128,128,128,0.25)",
            tickfont=dict(size=12),
            ticklen=0,
            categoryorder="array" if orientation == "v" else None,
            categoryarray=keys if orientation == "v" else None,
        ),
        margin=dict(pad=5),
    )

    if layout_kwargs:
        figure.update_layout(
            **layout_kwargs,
        )

    return figure