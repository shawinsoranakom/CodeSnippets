def _legacy_area_chart(
        self,
        data: "Data" = None,
        width: int = 0,
        height: int = 0,
        use_container_width: bool = True,
    ) -> "DeltaGenerator":
        """Display an area chart.

        This is just syntax-sugar around st._legacy_altair_chart. The main difference
        is this command uses the data's own column and indices to figure out
        the chart's spec. As a result this is easier to use for many "just plot
        this" scenarios, while being less customizable.

        If st._legacy_area_chart does not guess the data specification
        correctly, try specifying your desired chart using st._legacy_altair_chart.

        Parameters
        ----------
        data : pandas.DataFrame, pandas.Styler, numpy.ndarray, Iterable, or dict
            Data to be plotted.

        width : int
            The chart width in pixels. If 0, selects the width automatically.

        height : int
            The chart width in pixels. If 0, selects the height automatically.

        use_container_width : bool
            If True, set the chart width to the column width. This takes
            precedence over the width argument.

        Example
        -------
        >>> chart_data = pd.DataFrame(
        ...     np.random.randn(20, 3),
        ...     columns=['a', 'b', 'c'])
        ...
        >>> st._legacy_area_chart(chart_data)

        .. output::
           https://static.streamlit.io/0.50.0-td2L/index.html?id=Pp65STuFj65cJRDfhGh4Jt
           height: 220px

        """
        vega_lite_chart_proto = VegaLiteChartProto()

        chart = generate_chart("area", data, width, height)
        marshall(vega_lite_chart_proto, chart, use_container_width)
        last_index = last_index_for_melted_dataframes(data)

        return self.dg._enqueue(
            "area_chart", vega_lite_chart_proto, last_index=last_index
        )