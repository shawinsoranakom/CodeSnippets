def suppress_cached_st_function_warning() -> Iterator[None]:
    with MEMO_CALL_STACK.suppress_cached_st_function_warning(), SINGLETON_CALL_STACK.suppress_cached_st_function_warning():
        yield