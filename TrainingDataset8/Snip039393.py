def as_replay_test_data() -> MultiCacheResults:
    """Creates cached results for a function that returned 1
    and executed `st.text(1)`.
    """
    widget_key = _make_widget_key([], CacheType.MEMO)
    d = {}
    d[widget_key] = CachedResult(
        1,
        [ElementMsgData("text", TextProto(body="1"), st._main.id, "")],
        st._main.id,
        st.sidebar.id,
    )
    return MultiCacheResults(set(), d)