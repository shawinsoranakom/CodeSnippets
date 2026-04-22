def cache_clear():
    """Clear st.cache, st.memo, and st.singleton caches."""
    result = streamlit.runtime.legacy_caching.clear_cache()
    cache_path = streamlit.runtime.legacy_caching.get_cache_path()
    if result:
        print("Cleared directory %s." % cache_path)
    else:
        print("Nothing to clear at %s." % cache_path)

    streamlit.runtime.caching.memo.clear()
    streamlit.runtime.caching.singleton.clear()