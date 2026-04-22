def rerun() -> NoReturn:
    """Rerun the script immediately.

    When `st.experimental_rerun()` is called, the script is halted - no
    more statements will be run, and the script will be queued to re-run
    from the top.

    If this function is called outside of Streamlit, it will raise an
    Exception.
    """

    ctx = get_script_run_ctx()

    query_string = ""
    page_script_hash = ""
    if ctx is not None:
        query_string = ctx.query_string
        page_script_hash = ctx.page_script_hash

    raise RerunException(
        RerunData(
            query_string=query_string,
            page_script_hash=page_script_hash,
        )
    )