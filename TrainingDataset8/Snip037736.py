def maybe_show_cached_st_function_warning(dg, st_func_name: str) -> None:
    MEMO_CALL_STACK.maybe_show_cached_st_function_warning(dg, st_func_name)
    SINGLETON_CALL_STACK.maybe_show_cached_st_function_warning(dg, st_func_name)