def maybe_show_cached_st_function_warning(
    dg: "st.delta_generator.DeltaGenerator", st_func_name: str
) -> None:
    """If appropriate, warn about calling st.foo inside @cache.

    DeltaGenerator's @_with_element and @_widget wrappers use this to warn
    the user when they're calling st.foo() from within a function that is
    wrapped in @st.cache.

    Parameters
    ----------
    dg : DeltaGenerator
        The DeltaGenerator to publish the warning to.

    st_func_name : str
        The name of the Streamlit function that was called.

    """
    if (
        len(_cache_info.cached_func_stack) > 0
        and _cache_info.suppress_st_function_warning <= 0
    ):
        cached_func = _cache_info.cached_func_stack[-1]
        _show_cached_st_function_warning(dg, st_func_name, cached_func)