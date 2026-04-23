def _arrow_bar_chart(
        self,
        data: Data = None,
        *,
        x: Union[str, None] = None,
        y: Union[str, Sequence[str], None] = None,
        width: int = 0,
        height: int = 0,
        use_container_width: bool = True,
    ) -> "DeltaGenerator":
        """Display a bar chart.

        This is just syntax-sugar around st._arrow_altair_chart. The main difference
        is this command uses the data's own column and indices to figure out
        the chart's spec. As a result this is easier to use for many "just plot
        this" scenarios, while being less customizable.

        If st._arrow_bar_chart does not guess the data specification
        correctly, try specifying your desired chart using st._arrow_altair_chart.

        Parameters
        ----------
        data : pandas.DataFrame, pandas.Styler, pyarrow.Table, numpy.ndarray, Iterable, or dict
            Data to be plotted.

        x : str or None
            Column name to use for the x-axis. If None, uses the data index for the x-axis.
            This argument can only be supplied by keyword.

        y : str, sequence of str, or None
            Column name(s) to use for the y-axis. If a sequence of strings, draws several series
            on the same chart by melting your wide-format table into a long-format table behind
            the scenes. If None, draws the data of all remaining columns as data series.
            This argument can only be supplied by keyword.

        width : int
            The chart width in pixels. If 0, selects the width automatically.
            This argument can only be supplied by keyword.

        height : int
            The chart height in pixels. If 0, selects the height automatically.
            This argument can only be supplied by keyword.

        use_container_width : bool
            If True, set the chart width to the column width. This takes
            precedence over the width argument.
            This argument can only be supplied by keyword.

        Example
        -------
        >>> chart_data = pd.DataFrame(
        ...     np.random.randn(50, 3),
        ...     columns=["a", "b", "c"])
        ...
        >>> st._arrow_bar_chart(chart_data)

        .. output::
           https://static.streamlit.io/0.66.0-2BLtg/index.html?id=GaYDn6vxskvBUkBwsGVEaL
           height: 220px

        """

        proto = ArrowVegaLiteChartProto()
        chart = _generate_chart(ChartType.BAR, data, x, y, width, height)
        marshall(proto, chart, use_container_width, theme="streamlit")
        last_index = last_index_for_melted_dataframes(data)

        return self.dg._enqueue("arrow_bar_chart", proto, last_index=last_index)