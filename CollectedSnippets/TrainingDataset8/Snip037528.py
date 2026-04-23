def map(
        self,
        data: Data = None,
        zoom: Optional[int] = None,
        use_container_width: bool = True,
    ) -> "DeltaGenerator":
        """Display a map with points on it.

        This is a wrapper around st.pydeck_chart to quickly create scatterplot
        charts on top of a map, with auto-centering and auto-zoom.

        When using this command, we advise all users to use a personal Mapbox
        token. This ensures the map tiles used in this chart are more
        robust. You can do this with the mapbox.token config option.

        To get a token for yourself, create an account at
        https://mapbox.com. It's free! (for moderate usage levels). For more
        info on how to set config options, see
        https://docs.streamlit.io/library/advanced-features/configuration#set-configuration-options

        Parameters
        ----------
        data : pandas.DataFrame, pandas.Styler, pyarrow.Table, numpy.ndarray, pyspark.sql.DataFrame, snowflake.snowpark.dataframe.DataFrame, snowflake.snowpark.table.Table, Iterable, dict, or None
            The data to be plotted. Must have columns called 'lat', 'lon',
            'latitude', or 'longitude'.
        zoom : int
            Zoom level as specified in
            https://wiki.openstreetmap.org/wiki/Zoom_levels
        use_container_width: bool

        Example
        -------
        >>> import streamlit as st
        >>> import pandas as pd
        >>> import numpy as np
        >>>
        >>> df = pd.DataFrame(
        ...     np.random.randn(1000, 2) / [50, 50] + [37.76, -122.4],
        ...     columns=['lat', 'lon'])
        >>>
        >>> st.map(df)

        .. output::
           https://doc-map.streamlitapp.com/
           height: 650px

        """
        map_proto = DeckGlJsonChartProto()
        map_proto.json = to_deckgl_json(data, zoom)
        map_proto.use_container_width = use_container_width
        return self.dg._enqueue("deck_gl_json_chart", map_proto)