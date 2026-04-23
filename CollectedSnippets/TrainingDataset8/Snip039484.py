def tearDown(self):
        # Some of these tests reach directly into _cache_info and twiddle it.
        # Reset default values on teardown.
        caching._cache_info.cached_func_stack = []
        caching._cache_info.suppress_st_function_warning = 0
        super().tearDown()