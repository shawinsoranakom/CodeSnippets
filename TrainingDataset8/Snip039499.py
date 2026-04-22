def test_function_name_does_not_use_hashfuncs(self):
        """Hash funcs should only be used on arguments to a function,
        and not when computing the key for a function's unique MemCache.
        """

        str_hash_func = Mock(return_value=None)

        @st.cache(hash_funcs={str: str_hash_func})
        def foo(string_arg):
            return []

        # If our str hash_func is called multiple times, it's probably because
        # it's being used to compute the function's cache_key (as opposed to
        # the value_key). It should only be used to compute the value_key!
        foo("ahoy")
        str_hash_func.assert_called_once_with("ahoy")