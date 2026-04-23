def create_rrg_with_tails(
    ratios_data: "DataFrame",
    momentum_data: "DataFrame",
    study: str,
    benchmark_symbol: str,
    tail_periods: int,
    tail_interval: Literal["day", "week", "month"],
) -> "Figure":
    """Create The Relative Rotation Graph With Tails.

    Parameters
    ----------
    ratios_data : DataFrame
        The DataFrame containing the RS-Ratio values.
    momentum_data : DataFrame
        The DataFrame containing the RS-Momentum values.
    study : str
        The study that was selected when loading the raw data.
        If custom data is supplied, this will override the study for the chart titles.
    benchmark_symbol : str
        The symbol of the benchmark.
    tail_periods : int
        The number of periods to display in the tails.
    tail_interval : Literal["day", "week", "month"]

    Returns
    -------
    Figure
        Plotly GraphObjects Figure.
    """
    # pylint: disable=import-outside-toplevel
    from pandas import to_datetime
    from plotly import graph_objects as go

    symbols = ratios_data.columns.to_list()

    tail_dict = {"week": "W", "month": "ME"}
    ratios_data.index = to_datetime(ratios_data.index)
    momentum_data.index = to_datetime(momentum_data.index)

    if tail_interval != "day":
        ratios_data = ratios_data.resample(tail_dict[tail_interval]).last()
        momentum_data = momentum_data.resample(tail_dict[tail_interval]).last()
    ratios_data = ratios_data.iloc[-tail_periods:]
    momentum_data = momentum_data.iloc[-tail_periods:]
    _tail_periods = len(ratios_data)
    tail_title = (
        f"The Previous {_tail_periods} {tail_interval.capitalize()}s "
        f"Ending {ratios_data.index[-1].strftime('%Y-%m-%d')}"
    )
    x_min = ratios_data.min().min()
    x_max = ratios_data.max().max()
    y_min = momentum_data.min().min()
    y_max = momentum_data.max().max()
    # Create an empty list to store the scatter traces
    frames: list = []
    x_data = ratios_data
    y_data = momentum_data
    for i, date in enumerate(ratios_data.index):  # pylint: disable=unused-variable
        frame_data: list = []

        for j, symbol in enumerate(symbols):
            x_frame_data = x_data[symbol].iloc[: i + 1]
            y_frame_data = y_data[symbol].iloc[: i + 1]
            name = symbol.upper().replace("^", "").replace(":US", "")
            special_name = "-" in name or len(name) > 7
            marker_size = 34 if special_name else 30
            line_frame_trace = go.Scatter(
                x=x_frame_data,
                y=y_frame_data,
                mode="markers+lines",
                line=dict(color=color_sequence[j], width=2, dash="dash"),
                marker=dict(
                    size=5, color=color_sequence[j], line=dict(color="black", width=1)
                ),
                showlegend=False,
                opacity=0.3,
                name=name,
                text=name,
                hovertemplate="<b>%{fullData.name}</b>: "
                + "RS-Ratio: %{x:.4f}, "
                + "RS-Momentum: %{y:.4f}"
                + "<extra></extra>",
                hoverlabel=dict(font_size=10),
            )

            marker_frame_trace = go.Scatter(
                x=[x_frame_data.iloc[-1]],
                y=[y_frame_data.iloc[-1]],
                mode="markers+text",
                name=name,
                text=name,
                textposition="middle center",
                textfont=(
                    dict(size=10, color="black")
                    if len(symbol) < 4
                    else dict(size=7, color="black")
                ),
                line=dict(color=color_sequence[j], width=2, dash="dash"),
                marker=dict(
                    size=marker_size,
                    color=color_sequence[j],
                    line=dict(color="black", width=1),
                ),
                opacity=0.9,
                showlegend=False,
                hovertemplate="<b>%{fullData.name}</b>: RS-Ratio: %{x:.4f}, RS-Momentum: %{y:.4f}<extra></extra>",
            )

            frame_data.extend([line_frame_trace, marker_frame_trace])

        frames.append(go.Frame(data=frame_data, name=f"Frame {i}"))

    # Define the initial trace for the figure
    initial_trace = frames[0]["data"]

    padding = 0.1
    y_range = [y_min - padding * abs(y_min) - 0.3, y_max + padding * abs(y_max) + 0.3]
    x_range = [x_min - padding * abs(x_min) - 0.3, x_max + padding * abs(x_max) + 0.3]

    # Create the layout for the figure
    layout = go.Layout(
        title={
            "text": (
                f"Relative Rotation Against {benchmark_symbol.replace('^', '')} {study.capitalize()} For {tail_title}"
            ),
            "x": 0.5,
            "xanchor": "center",
            "font": dict(size=18),
        },
        xaxis=dict(
            title=dict(text="RS-Ratio", font=dict(size=16)),
            showgrid=True,
            zeroline=True,
            showline=True,
            mirror=True,
            ticklen=0,
            zerolinecolor="black",
            range=x_range,
            gridcolor="lightgrey",
            showspikes=False,
        ),
        yaxis=dict(
            title=dict(text="RS-Momentum", font=dict(size=16)),
            showgrid=True,
            zeroline=True,
            showline=True,
            mirror=True,
            ticklen=0,
            zerolinecolor="black",
            range=y_range,
            gridcolor="lightgrey",
            side="left",
            title_standoff=5,
        ),
        plot_bgcolor="rgba(255,255,255,1)",
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
        hovermode="closest",
        updatemenus=[
            {
                "buttons": [
                    {
                        "args": [
                            None,
                            {
                                "frame": {"duration": 500, "redraw": False},
                                "fromcurrent": True,
                                "transition": {"duration": 500, "easing": "linear"},
                            },
                        ],
                        "label": "Play",
                        "method": "animate",
                    }
                ],
                "direction": "left",
                "pad": {"r": 0, "t": 75},
                "showactive": False,
                "type": "buttons",
                "x": -0.025,
                "xanchor": "left",
                "y": 0,
                "yanchor": "top",
                "bgcolor": "rgba(150, 150, 150, 0.8)",
                "bordercolor": "rgba(100, 100, 100, 0.5)",
                "borderwidth": 1,
                "font": {"color": "black"},
            }
        ],
        sliders=[
            {
                "active": 0,
                "yanchor": "top",
                "xanchor": "center",
                "currentvalue": {
                    "font": {"size": 16},
                    "prefix": "Date: ",
                    "visible": True,
                    "xanchor": "right",
                },
                "transition": {"duration": 300, "easing": "cubic-in-out"},
                "pad": {"b": 10, "t": 50},
                "len": 0.9,
                "x": 0.5,
                "y": 0,
                "steps": [
                    {
                        "label": f"{x_data.index[i].strftime('%Y-%m-%d')}",
                        "method": "animate",
                        "args": [
                            [f"Frame {i}"],
                            {
                                "mode": "immediate",
                                "transition": {"duration": 300},
                                "frame": {"duration": 300, "redraw": False},
                            },
                        ],
                    }
                    for i in range(len(x_data.index))
                ],
            }
        ],
    )

    # Create the figure and add the initial trace
    fig = go.Figure(data=initial_trace, layout=layout, frames=frames)

    return fig