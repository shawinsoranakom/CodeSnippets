def economy_survey_bls_series(
        **kwargs,
    ) -> tuple["OpenBBFigure", dict[str, Any]]:
        """Economy Survey BLS Series Chart.

        Parameters
        ----------
        data: Optional[Union[DataFrame, List[Data]]]
            Filtered subset of the parent results.
        target_symbol: Optional[str]
            The target symbol(s) to plot. Plot multiple symbols by separating them with a comma. Max 10 symbols.
        target_col: Optional[str]
            The target column to plot. Default is 'value'.
        plot_type: Literal["line", "bar"]
            The type of plot to display. Default is 'line', unless the data is significantly small.
        normalize: bool
            Normalize the data before displaying. Default is False.
        title: Optional[str]
            The title of the chart.
        xtitle: Optional[str]
            The title of the x-axis.
        ytitle: Optional[str]
            The title of the y-axis.
        bar_kwargs: Optional[dict]
            Additional keyword arguments applied to `fig.add_bar`.
        scatter_kwargs: Optional[dict]
            Additional keyword arguments applied to `fig.add_scatter`.
        layout_kwargs: Optional[dict]
            Additional keyword arguments applied to `fig.update_layout`.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_charting.charts.generic_charts import bar_chart, line_chart
        from openbb_charting.charts.helpers import (
            z_score_standardization,
        )
        from openbb_core.app.utils import basemodel_to_df
        from pandas import DataFrame

        provider = kwargs.get("provider")

        if provider != "bls":
            raise RuntimeError(
                f"This charting method does not support {provider}. Supported providers: bls."
            )

        _data = (
            kwargs.pop("data", None)
            if "data" in kwargs and kwargs["data"] is not None
            else kwargs.get("obbject_item")
        )
        df = DataFrame()

        if isinstance(_data, DataFrame) and not _data.empty:
            df = _data.reset_index() if _data.index.name == "date" else _data
        else:
            try:
                df = basemodel_to_df(_data, index=None)  # type: ignore
            except Exception as e:
                raise RuntimeError("Unable to process supplied data.") from e

        if df.empty or len(df) < 2:
            raise RuntimeError("No data found to plot.")

        cols = df.columns.to_list()
        target_col = kwargs.get("target_col", "value")
        if target_col not in cols:
            raise RuntimeError(f"Column '{target_col}' not found in the data.")

        new_df = df.pivot(columns="symbol", values=target_col, index="date")
        target_symbols = kwargs.get("target_symbol", "").split(",")[:10]  # type: ignore

        if not target_symbols or len(target_symbols) == 0 or target_symbols[0] == "":
            target_symbols = new_df.columns.to_list()[:10]

        metadata = kwargs["extra"].get("results_metadata", {})  # type: ignore
        ytitle = kwargs.get("ytitle", "")

        new_df = new_df.filter(target_symbols, axis=1)

        if "percent" in target_col.lower():  # type: ignore
            ytitle = (
                ytitle
                if ytitle
                else target_col.replace("change_percent_", "").replace("M", " Month") + " Change (%)"  # type: ignore
            )
            new_df = new_df.apply(lambda x: x * 100)
        elif "change" in target_col.lower() and "percent" not in target_col.lower():  # type: ignore
            ytitle = (
                ytitle if ytitle else target_col.replace("change_", "").replace("M", " Month") + " Change"  # type: ignore
            )

        title_map: dict = {}
        for symbol in target_symbols:
            if symbol not in new_df.columns:
                continue
            survey_name = metadata.get(symbol, {}).get("survey_name", symbol)  # type: ignore
            series_title = metadata.get(symbol, {}).get("series_title", symbol)  # type: ignore

            if survey_name != series_title:
                title_map[symbol] = f"{survey_name} \n    {series_title}"

        normalize = kwargs.get("normalize", False)
        same_axis = kwargs.get("same_axis", False)

        if normalize:
            new_df = new_df.apply(z_score_standardization)
            same_axis = True
            if ytitle:
                ytitle = f"Normalized {ytitle.replace('(%)', '')}"  # type: ignore

        plot_type = kwargs.get("plot_type")

        if plot_type is None:
            plot_type = (
                "line" if (len(new_df.index) > 36 and len(new_df.columns.to_list()) >= 1) else "bar"  # type: ignore
            )

        layout_kwargs: dict = kwargs.pop("layout_kwargs", {})  # type: ignore
        scatter_kwargs: dict = kwargs.pop("scatter_kwargs", {})  # type: ignore
        bar_kwargs: dict = kwargs.pop("bar_kwargs", {})  # type: ignore
        hovertemplate = scatter_kwargs.pop("hovertemplate", None)  # type: ignore
        trace_titles = {
            symbol: metadata.get(symbol, {})
            .get("series_title", symbol)
            .replace(",", " -")
            for symbol in target_symbols
        }
        new_df.columns = [trace_titles.get(col, col) for col in new_df.columns]
        scatter_kwargs["hovertemplate"] = (  # type: ignore
            hovertemplate if hovertemplate else "%{fullData.name}:%{y}<extra></extra>"
        )

        if len(target_symbols) == 1:
            title = title_map.get(target_symbols[0], target_symbols[0])
            fig = (
                line_chart(
                    data=new_df,
                    title=title,
                    ytitle=ytitle,
                    y=list(trace_titles.values()),
                    scatter_kwargs=scatter_kwargs,
                    layout_kwargs=layout_kwargs,
                    **kwargs,
                )
                if plot_type == "line"
                else bar_chart(
                    data=new_df,
                    title=title,
                    ytitle=ytitle,
                    x=new_df.index,  # type: ignore
                    y=list(trace_titles.values()),
                    layout_kwargs=layout_kwargs,
                    bar_kwargs=bar_kwargs,
                    **kwargs,
                )
            )
        else:
            survey_name = metadata.get(target_symbols[0], {}).get("survey_name", target_symbols[0]).split("\n")[0].strip()  # type: ignore
            _t = kwargs.pop("title", None)
            title = _t if _t else f"{survey_name} - {ytitle}" if ytitle else survey_name
            fig = (
                line_chart(
                    data=new_df,
                    y=list(trace_titles.values()),
                    title=title,
                    ytitle=ytitle,
                    same_axis=same_axis,
                    normalize=False,
                    scatter_kwargs=scatter_kwargs,
                    layout_kwargs=layout_kwargs,
                    **kwargs,
                )
                if plot_type == "line"
                else bar_chart(
                    data=new_df,
                    title=title,
                    ytitle=ytitle,
                    x=new_df.index,  # type: ignore
                    y=list(trace_titles.values()),
                    layout_kwargs=layout_kwargs,
                    bar_kwargs=bar_kwargs,
                    **kwargs,
                )
            )

        fig.update_layout(
            margin=dict(b=20),
            legend=dict(
                orientation="h",
                yanchor="top",
                xanchor="left",
                y=-0.075,
                x=0,
                font=dict(size=12),
            ),
        )
        content = fig.to_plotly_json()

        return fig, content