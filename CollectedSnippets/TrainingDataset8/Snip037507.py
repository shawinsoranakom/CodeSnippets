def _legacy_altair_chart(
        self, altair_chart: "Chart", use_container_width: bool = False
    ) -> "DeltaGenerator":
        """Display a chart using the Altair library.

        Parameters
        ----------
        altair_chart : altair.vegalite.v4.api.Chart
            The Altair chart object to display.

        use_container_width : bool
            If True, set the chart width to the column width. This takes
            precedence over Altair's native `width` value.

        Example
        -------

        >>> import pandas as pd
        >>> import numpy as np
        >>> import altair as alt
        >>>
        >>> df = pd.DataFrame(
        ...     np.random.randn(200, 3),
        ...     columns=['a', 'b', 'c'])
        ...
        >>> c = alt.Chart(df).mark_circle().encode(
        ...     x='a', y='b', size='c', color='c', tooltip=['a', 'b', 'c'])
        >>>
        >>> st._legacy_altair_chart(c, use_container_width=True)

        .. output::
           https://static.streamlit.io/0.25.0-2JkNY/index.html?id=8jmmXR8iKoZGV4kXaKGYV5
           height: 200px

        Examples of Altair charts can be found at
        https://altair-viz.github.io/gallery/.

        """
        vega_lite_chart_proto = VegaLiteChartProto()

        marshall(
            vega_lite_chart_proto,
            altair_chart,
            use_container_width=use_container_width,
        )
        return self.dg._enqueue("vega_lite_chart", vega_lite_chart_proto)