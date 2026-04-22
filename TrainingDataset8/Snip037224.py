def set_query_params(**query_params: Any) -> None:
    """Set the query parameters that are shown in the browser's URL bar.

    Parameters
    ----------
    **query_params : dict
        The query parameters to set, as key-value pairs.

    Example
    -------

    To point the user's web browser to something like
    "http://localhost:8501/?show_map=True&selected=asia&selected=america",
    you would do the following:

    >>> st.experimental_set_query_params(
    ...     show_map=True,
    ...     selected=["asia", "america"],
    ... )

    """
    ctx = get_script_run_ctx()
    if ctx is None:
        return
    ctx.query_string = parse.urlencode(query_params, doseq=True)
    msg = ForwardMsg()
    msg.page_info_changed.query_string = ctx.query_string
    ctx.enqueue(msg)