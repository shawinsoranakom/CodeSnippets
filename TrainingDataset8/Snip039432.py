def tearDown(self):
        st.experimental_singleton.clear()
        # Some of these tests reach directly into _cache_info and twiddle it.
        # Reset default values on teardown.
        singleton_decorator.SINGLETON_CALL_STACK._cached_func_stack = []
        singleton_decorator.SINGLETON_CALL_STACK._suppress_st_function_warning = 0