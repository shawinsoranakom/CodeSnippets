def altair_chart(
        self,
        altair_chart: "Chart",
        use_container_width: bool = False,
        theme: Union[None, Literal["streamlit"]] = "streamlit",
    ) -> "DeltaGenerator":
        """Display a chart using the Altair library.

        Parameters
        ----------
        altair_chart : altair.vegalite.v2.api.Chart
            The Altair chart object to display.

        use_container_width : bool
            If True, set the chart width to the column width. This takes
            precedence over Altair's native `width` value.

        theme : "streamlit" or None
            The theme of the chart. Currently, we only support "streamlit" for the Streamlit
            defined design or None to fallback to the default behavior of the library.

        Example
        -------

        >>> import pandas as pd
        >>> import numpy as np
        >>> import altair as alt
        >>>
        >>> chart_data = pd.DataFrame(
        ...     np.random.randn(20, 3),
        ...     columns=['a', 'b', 'c'])
        ...
        >>> c = alt.Chart(chart_data).mark_circle().encode(
        ...     x='a', y='b', size='c', color='c', tooltip=['a', 'b', 'c'])
        >>>
        >>> st.altair_chart(c, use_container_width=True)

        Examples of Altair charts can be found at
        https://altair-viz.github.io/gallery/.

        .. output::
           https://doc-vega-lite-chart.streamlitapp.com/
           height: 300px

        """

        if _use_arrow():
            return self.dg._arrow_altair_chart(altair_chart, use_container_width, theme)
        else:
            return self.dg._legacy_altair_chart(altair_chart, use_container_width)