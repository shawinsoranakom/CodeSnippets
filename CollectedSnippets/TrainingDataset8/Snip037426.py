def vega_lite_chart(
        self,
        data: "Data" = None,
        spec: Optional[Dict[str, Any]] = None,
        use_container_width: bool = False,
        theme: Union[None, Literal["streamlit"]] = "streamlit",
        **kwargs: Any,
    ) -> "DeltaGenerator":
        """Display a chart using the Vega-Lite library.

        Parameters
        ----------
        data : pandas.DataFrame, pandas.Styler, pyarrow.Table, numpy.ndarray, Iterable, dict, or None
            Either the data to be plotted or a Vega-Lite spec containing the
            data (which more closely follows the Vega-Lite API).
            Pyarrow tables are not supported by Streamlit's legacy DataFrame serialization
            (i.e. with `config.dataFrameSerialization = "legacy"`).
            To use pyarrow tables, please enable pyarrow by changing the config setting,
            `config.dataFrameSerialization = "arrow"`.

        spec : dict or None
            The Vega-Lite spec for the chart. If the spec was already passed in
            the previous argument, this must be set to None. See
            https://vega.github.io/vega-lite/docs/ for more info.

        use_container_width : bool
            If True, set the chart width to the column width. This takes
            precedence over Vega-Lite's native `width` value.

        theme : "streamlit" or None
            The theme of the chart. Currently, we only support "streamlit" for the Streamlit
            defined design or None to fallback to the default behavior of the library.

        **kwargs : any
            Same as spec, but as keywords.

        Example
        -------
        >>> import pandas as pd
        >>> import numpy as np
        >>>
        >>> chart_data = pd.DataFrame(
        ...     np.random.randn(200, 3),
        ...     columns=['a', 'b', 'c'])
        >>>
        >>> st.vega_lite_chart(chart_data, {
        ...     'mark': {'type': 'circle', 'tooltip': True},
        ...     'encoding': {
        ...         'x': {'field': 'a', 'type': 'quantitative'},
        ...         'y': {'field': 'b', 'type': 'quantitative'},
        ...         'size': {'field': 'c', 'type': 'quantitative'},
        ...         'color': {'field': 'c', 'type': 'quantitative'},
        ...     },
        ... })

        .. output::
           https://doc-vega-lite-chart.streamlitapp.com/
           height: 300px

        Examples of Vega-Lite usage without Streamlit can be found at
        https://vega.github.io/vega-lite/examples/. Most of those can be easily
        translated to the syntax shown above.

        """
        if _use_arrow():
            return self.dg._arrow_vega_lite_chart(
                data, spec, use_container_width, theme, **kwargs
            )
        else:
            return self.dg._legacy_vega_lite_chart(
                data, spec, use_container_width, **kwargs
            )