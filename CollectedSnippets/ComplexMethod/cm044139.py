def _ta_ma(**kwargs):
    """Plot moving average helper."""
    # pylint: disable=import-outside-toplevel
    from openbb_charting.core.chart_style import ChartStyle
    from openbb_charting.core.openbb_figure import OpenBBFigure
    from openbb_core.app.utils import basemodel_to_df
    from pandas import DataFrame

    index = (
        kwargs.get("index")
        if "index" in kwargs and kwargs.get("index") is not None
        else "date"
    )
    data = kwargs.get("data")
    ma_type = (
        kwargs["ma_type"]
        if "ma_type" in kwargs and kwargs.get("ma_type") is not None
        else "sma"
    )
    ma_types = ma_type.split(",") if isinstance(ma_type, str) else ma_type

    if isinstance(data, DataFrame) and not data.empty:
        data = data.set_index(index) if index in data.columns else data

    if data is None:
        data = basemodel_to_df(kwargs["obbject_item"], index=index)

    if isinstance(data, list):
        data = basemodel_to_df(data, index=index)

    window = (
        kwargs.get("length", [])
        if "length" in kwargs and kwargs.get("length") is not None
        else [50]
    )
    offset = kwargs.get("offset", 0)
    target = (
        kwargs.get("target")
        if "target" in kwargs and kwargs.get("target") is not None
        else "close"
    )

    if target not in data.columns and "close" in data.columns:
        target = "close"

    if target not in data.columns and "close" not in data.columns:
        raise ValueError(f"Column '{target}', or 'close', not found in the data.")

    df = data.copy()
    if target in data.columns:
        df = df[[target]]
        df.columns = ["close"]
    title = (
        kwargs.get("title")
        if "title" in kwargs and kwargs.get("title") is not None
        else f"{ma_type.upper()}"
    )

    fig = OpenBBFigure()
    fig = fig.create_subplots(
        1,
        1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        horizontal_spacing=0.01,
        row_width=[1],
        specs=[[{"secondary_y": True}]],
    )
    fig.update_layout(ChartStyle().plotly_template.get("layout", {}))
    font_color = "black" if ChartStyle().plt_style == "light" else "white"
    ma_df = DataFrame()
    window = [window] if isinstance(window, int) else window
    for w in window:
        for ma_type in ma_types:
            ma_df[f"{ma_type.upper()} {w}"] = getattr(df.ta, ma_type)(
                length=w, offset=offset
            )

    if kwargs.get("dropnan") is True:
        ma_df = ma_df.dropna()
        data = data.iloc[-len(ma_df) :]

    if (
        "candles" in kwargs
        and kwargs.get("candles") is True
        and kwargs.get("target") is None
    ):
        volume = kwargs.get("volume") is True
        fig, _ = to_chart(data, candles=True, volume=volume)

    else:
        ma_df[f"{target}".title()] = data[target]

    for i, col in enumerate(ma_df.columns):
        name = col.replace("_", " ")
        fig.add_scatter(
            x=ma_df.index,
            y=ma_df[col],
            name=name,
            mode="lines",
            hovertemplate=f"{name}: %{{y}}<extra></extra>",
            line=dict(width=1, color=LARGE_CYCLER[i]),
            showlegend=True,
        )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=16)),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            xanchor="right",
            y=1.02,
            x=0.95,
            bgcolor="rgba(0,0,0,0)" if font_color == "white" else "rgba(255,255,255,0)",
        ),
        xaxis=dict(
            ticklen=0,
            showgrid=True,
            gridcolor="rgba(128,128,128,0.3)",
            zeroline=True,
            mirror=True,
        ),
        yaxis=dict(
            ticklen=0,
            showgrid=True,
            gridcolor="rgba(128,128,128,0.3)",
            zeroline=True,
            mirror=True,
            autorange=True,
        ),
        font=dict(color=font_color),
    )

    content = fig.show(external=True).to_plotly_json()

    return fig, content