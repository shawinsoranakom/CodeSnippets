def _show_cached_st_function_warning(
    dg: "st.delta_generator.DeltaGenerator",
    st_func_name: str,
    cached_func: Callable[..., Any],
) -> None:
    # Avoid infinite recursion by suppressing additional cached
    # function warnings from within the cached function warning.
    with suppress_cached_st_function_warning():
        e = CachedStFunctionWarning(st_func_name, cached_func)
        dg.exception(e)