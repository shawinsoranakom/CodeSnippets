def test_function_body_uses_hashfuncs(self):
        hash_func = Mock(return_value=None)

        # This is an external object that's referenced by our
        # function. It cannot be hashed (without a custom hashfunc).
        dict_gen = {1: (x for x in range(1))}

        @st.cache(hash_funcs={"builtins.generator": hash_func})
        def foo(arg):
            # Reference the generator object. It will be hashed when we
            # hash the function body to generate foo's cache_key.
            print(dict_gen)
            return []

        foo(1)
        foo(2)
        hash_func.assert_called_once()