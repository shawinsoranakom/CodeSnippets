def bar_chart(  # noqa: PLR0912
    data: Union[
        list,
        dict,
        "DataFrame",
        list["DataFrame"],
        "Series",
        list["Series"],
        "ndarray",
        Data,
    ],
    x: str,
    y: str | list[str],
    barmode: Literal["group", "stack", "relative", "overlay"] = "group",
    xtype: Literal["category", "multicategory", "date", "log", "linear"] = "category",
    title: str | None = None,
    xtitle: str | None = None,
    ytitle: str | None = None,
    orientation: Literal["h", "v"] = "v",
    colors: list[str] | None = None,
    bar_kwargs: dict[str, Any] | None = None,
    layout_kwargs: dict[str, Any] | None = None,
    **kwargs,
) -> Union["OpenBBFigure", "Figure"]:
    """Create a vertical bar chart on a single x-axis with one or more values for the y-axis.

    Parameters
    ----------
    data : Union[
        list, dict, "DataFrame", List["DataFrame"], "Series", List["Series"], "ndarray", Data
    ]
        Data to plot.
    x : str
        The x-axis column name.
    y : Union[str, List[str]]
        The y-axis column name(s).
    barmode : Literal["group", "stack", "relative", "overlay"], optional
        The bar mode, by default "group".
    xtype : Literal["category", "multicategory", "date", "log", "linear"], optional
        The x-axis type, by default "category".
    title : str, optional
        The title of the chart, by default None.
    xtitle : str, optional
        The x-axis title, by default None.
    ytitle : str, optional
        The y-axis title, by default None.
    colors: List[str], optional
        Manually set the colors to cycle through for each column in 'y', by default None.
    bar_kwargs : Dict[str, Any], optional
        Additional keyword arguments to apply with figure.add_bar(), by default None.
    layout_kwargs : Dict[str, Any], optional
        Additional keyword arguments to apply with figure.update_layout(), by default None.

    Returns
    -------
    OpenBBFigure
        The OpenBBFigure object.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_charting.core.openbb_figure import OpenBBFigure

    try:
        figure = OpenBBFigure()
    except Exception as _:
        figure = OpenBBFigure(create_backend=True)

    figure = figure.create_subplots(
        1,
        1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        horizontal_spacing=0.01,
        row_width=[1],
        specs=[[{"secondary_y": True}]],
    )

    text_color = "white" if ChartStyle().plt_style == "dark" else "black"
    if colors is not None:
        figure.update_layout(colorway=colors)
    if bar_kwargs is None:
        bar_kwargs = {}
    if isinstance(data, (Data, list, dict)):
        data = basemodel_to_df(convert_to_basemodel(data), index=None)

    bar_df = data.copy().set_index(x)  # type: ignore
    y = y.split(",") if isinstance(y, str) else y
    hovertemplate = bar_kwargs.pop("hovertemplate", None)
    width = bar_kwargs.pop("width", None)
    for item in y:
        figure.add_bar(
            x=bar_df.index if orientation == "v" else bar_df[item],
            y=bar_df[item] if orientation == "v" else bar_df.index,
            name=bar_df[item].name,
            showlegend=len(y) > 1,
            legendgroup=bar_df[item].name,
            orientation=orientation,
            hovertemplate=(
                hovertemplate
                if hovertemplate
                else (
                    "%{fullData.name}:%{y}<extra></extra>"
                    if orientation == "v"
                    else "%{fullData.name}:%{x}<extra></extra>"
                )
            ),
            width=(
                width
                if width
                else 0.95 / len(y) * 0.75 if barmode == "group" and len(y) > 1 else 0.95
            ),
            **bar_kwargs,
        )

    figure.update_layout(
        title=dict(text=title if title else None, x=0.5, font=dict(size=16)),
        legend=dict(
            orientation="v",
            yanchor="top",
            xanchor="right",
            y=0.95,
            x=-0.01 if orientation == "v" else 1.01,
            xref="paper",
            font=dict(size=12),
            bgcolor=(
                "rgba(0,0,0,0)" if text_color == "white" else "rgba(255,255,255,0)"
            ),
        ),
        xaxis=dict(
            type=xtype,
            title=dict(
                text=xtitle if xtitle else None, standoff=30, font=dict(size=16)
            ),
            ticklen=0,
            showgrid=orientation == "h",
            tickfont=dict(size=12, family="sans-serif"),
            categoryorder="array" if orientation == "v" else None,
            categoryarray=bar_df.index if orientation == "v" else None,
        ),
        yaxis=dict(
            title=dict(
                text=ytitle if ytitle else None, standoff=30, font=dict(size=16)
            ),
            ticklen=0,
            showgrid=orientation == "v",
            tickfont=dict(size=12),
            side="left" if orientation == "h" else "right",
            categoryorder="array" if orientation == "h" else None,
            categoryarray=bar_df.index if orientation == "h" else None,
        ),
        margin=dict(pad=5),
        barmode=barmode,
    )
    if orientation == "h":
        figure.update_layout(
            xaxis=dict(
                type="linear",
                showspikes=False,
            ),
            yaxis=dict(
                type="category",
                showspikes=False,
            ),
            hoverlabel=dict(
                font=dict(size=12),
            ),
            hovermode="y unified",
        )
    if layout_kwargs:
        figure.update_layout(
            **layout_kwargs,
        )
    return figure