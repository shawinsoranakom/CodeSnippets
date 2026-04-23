def technical_relative_rotation(
        **kwargs: Any,
    ) -> tuple["OpenBBFigure", dict[str, Any]]:
        """Relative Rotation Chart."""
        # pylint: disable=import-outside-toplevel
        from openbb_charting.charts import relative_rotation  # noqa
        from openbb_charting.core.chart_style import ChartStyle  # noqa
        from openbb_charting.core.openbb_figure import OpenBBFigure  # noqa
        from openbb_core.app.utils import basemodel_to_df  # noqa

        ratios_df = basemodel_to_df(kwargs["obbject_item"].rs_ratios, index="date")  # type: ignore
        momentum_df = basemodel_to_df(kwargs["obbject_item"].rs_momentum, index="date")  # type: ignore
        benchmark_symbol = kwargs["obbject_item"].benchmark  # type: ignore
        study = kwargs.get("study")
        study = str(kwargs["obbject_item"].study) if study is None else str(study)
        show_tails = kwargs.get("show_tails")
        show_tails = True if show_tails is None else show_tails
        tail_periods = int(kwargs.get("tail_periods")) if "tail_periods" in kwargs else 16  # type: ignore
        tail_interval = str(kwargs.get("tail_interval")) if "tail_interval" in kwargs else "week"  # type: ignore
        date = kwargs.get("date") if "date" in kwargs else None  # type: ignore
        show_tails = False if date is not None else show_tails
        if ratios_df.empty or momentum_df.empty:
            raise RuntimeError("Error: No data to plot.")

        if show_tails is True:
            fig = relative_rotation.create_rrg_with_tails(
                ratios_df,
                momentum_df,
                study,
                benchmark_symbol,
                tail_periods,
                tail_interval,  # type: ignore
            )

        if show_tails is False:
            fig = relative_rotation.create_rrg_without_tails(
                ratios_df,
                momentum_df,
                benchmark_symbol,
                study,
                date,  # type: ignore
            )

        figure = OpenBBFigure(fig)  # pylint: disable=E0606
        font_color = "black" if ChartStyle().plt_style == "light" else "white"
        figure.update_layout(
            plot_bgcolor="rgba(255,255,255,1)",
            font=dict(color=font_color),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(128,128,128,0.3)",
                side="left",
                showline=True,
                zeroline=True,
                mirror=True,
                ticklen=0,
                tickfont=dict(size=14),
                title=dict(font=dict(size=16)),
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(128,128,128,0.3)",
                showline=True,
                zeroline=True,
                mirror=True,
                ticklen=0,
                tickfont=dict(size=14),
                title=dict(font=dict(size=16)),
                hoverformat="",
            ),
            hoverlabel=dict(
                font_size=12,
            ),
        )

        if kwargs.get("title") is not None:
            figure.set_title(str(kwargs.get("title")))
        content = figure.to_plotly_json()

        return figure, content