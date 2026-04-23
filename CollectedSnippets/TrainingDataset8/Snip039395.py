def tearDown(self):
        # Some of these tests reach directly into _cache_info and twiddle it.
        # Reset default values on teardown.
        memo_decorator.MEMO_CALL_STACK._cached_func_stack = []
        memo_decorator.MEMO_CALL_STACK._suppress_st_function_warning = 0
        st.experimental_memo.clear()