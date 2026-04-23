def _plot_to_url_or_load_cached_url(*args: Any, **kwargs: Any) -> "go.Figure":
    """Call plotly.plot wrapped in st.cache.

    This is so we don't unnecessarily upload data to Plotly's SASS if nothing
    changed since the previous upload.
    """
    try:
        # Plotly 4 changed its main package.
        import chart_studio.plotly as ply
    except ImportError:
        import plotly.plotly as ply

    return ply.plot(*args, **kwargs)