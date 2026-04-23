def create_rrg_without_tails(
    ratios_data: "DataFrame",
    momentum_data: "DataFrame",
    benchmark_symbol: str,
    study: str,
    date: dateType | None = None,
) -> "Figure":
    """Create the Plotly Figure Object without Tails.

    Parameters
    ----------
    ratios_data : DataFrame
        The DataFrame containing the RS-Ratio values.
    momentum_data : DataFrame
        The DataFrame containing the RS-Momentum values.
    benchmark_symbol : str
        The symbol of the benchmark.
    study: str
        The study that was selected when loading the raw data.
        If custom data is supplied, this will override the study for the chart titles.
    date : Optional[dateType], optional
        A specific date within the data to target for display, by default None.

    Returns
    -------
    Figure
        Plotly GraphObjects Figure.
    """
    # pylint: disable=import-outside-toplevel
    from plotly import graph_objects as go  # noqa
    from pandas import to_datetime  # noqa

    if date is not None and date not in ratios_data.index.astype(str):
        warn(f"Date {str(date)} not found in data, using the last available date.")
        date = ratios_data.index[-1]
    if date is None:
        date = ratios_data.index[-1]

    # Select a single row from each dataframe
    row_x = ratios_data.loc[to_datetime(date).date()]  # type: ignore
    row_y = momentum_data.loc[to_datetime(date).date()]  # type: ignore

    x_max = row_x.max() + 0.5
    x_min = row_x.min() - 0.5
    y_max = row_y.max() + 0.5
    y_min = row_y.min() - 0.5

    # Create an empty list to store the scatter traces
    traces = []

    # Loop through each column in the row_x dataframe
    for i, (column_name, value_x) in enumerate(row_x.items()):
        # Retrieve the corresponding value from the row_y dataframe
        value_y = row_y[column_name]  # type: ignore
        marker_name = column_name.upper().replace("^", "").replace(":US", "")  # type: ignore
        special_name = "-" in marker_name or len(marker_name) > 5
        marker_size = 38 if special_name else 30
        # Create a scatter trace for each column
        trace = go.Scatter(
            x=[value_x],
            y=[value_y],
            mode="markers+text",
            text=[marker_name],
            textposition="middle center",
            textfont=dict(size=10 if len(marker_name) < 4 else 8, color="black"),
            marker=dict(
                size=marker_size,
                color=color_sequence[i % len(color_sequence)],
                line=dict(color="black", width=1),
            ),
            name=column_name,
            showlegend=False,
            hovertemplate="<b>%{fullData.name}</b>"
            + "<br>RS-Ratio: %{x:.4f}</br>"
            + "RS-Momentum: %{y:.4f}"
            + "<extra></extra>",
        )
        # Add the trace to the list
        traces.append(trace)

    padding = 0.1
    y_range = [y_min - padding * abs(y_min) - 0.3, y_max + padding * abs(y_max)]
    x_range = [x_min - padding * abs(x_min), x_max + padding * abs(x_max)]

    layout = go.Layout(
        title={
            "text": (
                f"RS-Ratio vs RS-Momentum of {study.capitalize()} "
                f"Against {benchmark_symbol.replace('^', '')} - {to_datetime(row_x.name).strftime('%Y-%m-%d')}"  # type: ignore
            ),
            "x": 0.5,
            "xanchor": "center",
            "font": dict(size=20),
        },
        xaxis=dict(
            title="RS-Ratio",
            zerolinecolor="black",
            range=x_range,
            showspikes=False,
        ),
        yaxis=dict(
            title="<br>RS-Momentum",
            zerolinecolor="black",
            range=y_range,
            side="left",
            title_standoff=5,
            showspikes=False,
        ),
        shapes=[
            go.layout.Shape(
                type="rect",
                xref="x",
                yref="y",
                x0=0,
                y0=0,
                x1=x_range[1],
                y1=y_range[1],
                fillcolor="lightgreen",
                opacity=0.3,
                layer="below",
                line_width=0,
            ),
            go.layout.Shape(
                type="rect",
                xref="x",
                yref="y",
                x0=x_range[0],
                y0=0,
                x1=0,
                y1=y_range[1],
                fillcolor="lightblue",
                opacity=0.3,
                layer="below",
                line_width=0,
            ),
            go.layout.Shape(
                type="rect",
                xref="x",
                yref="y",
                x0=x_range[0],
                y0=y_range[0],
                x1=0,
                y1=0,
                fillcolor="lightpink",
                opacity=0.3,
                layer="below",
                line_width=0,
            ),
            go.layout.Shape(
                type="rect",
                xref="x",
                yref="y",
                x0=0,
                y0=y_range[0],
                x1=x_range[1],
                y1=0,
                fillcolor="lightyellow",
                opacity=0.3,
                layer="below",
                line_width=0,
            ),
            go.layout.Shape(
                type="rect",
                xref="x",
                yref="y",
                x0=x_range[0],
                y0=y_range[0],
                x1=x_range[1],
                y1=y_range[1],
                line=dict(
                    color="Black",
                    width=1,
                ),
                fillcolor="rgba(0,0,0,0)",
                layer="above",
            ),
        ],
        annotations=[
            go.layout.Annotation(
                x=1,
                xref="paper",
                y=1,
                yref="paper",
                text="Leading",
                showarrow=False,
                font=dict(
                    size=18,
                    color="darkgreen",
                ),
            ),
            go.layout.Annotation(
                x=1,
                xref="paper",
                y=0,
                yref="paper",
                text="Weakening",
                showarrow=False,
                font=dict(
                    size=18,
                    color="goldenrod",
                ),
            ),
            go.layout.Annotation(
                x=0,
                xref="paper",
                y=0,
                yref="paper",
                text="Lagging",
                showarrow=False,
                font=dict(
                    size=18,
                    color="red",
                ),
            ),
            go.layout.Annotation(
                x=0,
                xref="paper",
                yref="paper",
                y=1,
                text="Improving",
                showarrow=False,
                font=dict(
                    size=18,
                    color="blue",
                ),
            ),
        ],
        autosize=True,
        margin=dict(
            l=30,
            r=50,
            b=50,
            t=50,
            pad=0,
        ),
        dragmode="pan",
    )

    fig = go.Figure(data=traces, layout=layout)

    return fig