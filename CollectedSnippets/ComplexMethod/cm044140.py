def technical_cones(**kwargs) -> tuple["OpenBBFigure", dict[str, Any]]:
        """Volatility Cones Chart."""
        # pylint: disable=import-outside-toplevel
        from openbb_charting.core.chart_style import ChartStyle
        from openbb_charting.core.openbb_figure import OpenBBFigure
        from openbb_core.app.utils import basemodel_to_df
        from pandas import DataFrame

        data = kwargs.get("data")

        if isinstance(data, DataFrame) and not data.empty and "window" in data.columns:
            df_ta = data.set_index("window")
        else:
            df_ta = basemodel_to_df(kwargs["obbject_item"], index="window")  # type: ignore

        df_ta.columns = [col.title().replace("_", " ") for col in df_ta.columns]

        # Check if the data is formatted as expected.
        if not all(
            col in df_ta.columns for col in ["Realized", "Min", "Median", "Max"]
        ):
            raise ValueError("Data supplied does not match the expected format.")

        model = (
            str(kwargs.get("model"))
            .replace("std", "Standard Deviation")
            .replace("_", "-")
            .title()
            if kwargs.get("model")
            else "Standard Deviation"
        )

        symbol = str(kwargs.get("symbol")) + " - " if kwargs.get("symbol") else ""

        title = (
            str(kwargs.get("title"))
            if kwargs.get("title")
            else f"{symbol}Realized Volatility Cones - {model} Model"
        )

        colors = [
            "green",
            "red",
            "burlywood",
            "grey",
            "orange",
            "blue",
        ]

        fig = OpenBBFigure()

        fig.update_layout(ChartStyle().plotly_template.get("layout", {}))

        text_color = "black" if ChartStyle().plt_style == "light" else "white"

        for i, col in enumerate(df_ta.columns):
            fig.add_scatter(
                x=df_ta.index,
                y=df_ta[col],
                name=col,
                mode="lines+markers",
                hovertemplate=f"{col}: %{{y}}<extra></extra>",
                marker=dict(
                    color=colors[i],
                    size=11,
                ),
            )

        fig.set_title(title)

        fig.update_layout(
            font=dict(color=text_color),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                xanchor="right",
                y=1.02,
                x=1,
                bgcolor=(
                    "rgba(0,0,0,0)" if text_color == "white" else "rgba(255,255,255,0)"
                ),
            ),
            yaxis=dict(
                ticklen=0,
                showgrid=True,
                showline=True,
                mirror=True,
                zeroline=False,
                gridcolor="rgba(128,128,128,0.3)",
            ),
            xaxis=dict(
                type="category",
                tickmode="array",
                ticklen=0,
                tickvals=df_ta.index,
                ticktext=df_ta.index,
                title_text="Period",
                showgrid=False,
                showline=True,
                mirror=True,
                zeroline=False,
            ),
            margin=dict(l=20, r=20, b=20),
            dragmode="pan",
        )

        content = fig.to_plotly_json()

        return fig, content