def test_recursive_hash_func(self):
        def hash_int(x):
            return x

        @st.cache(hash_funcs={int: hash_int})
        def foo(x):
            return x

        self.assertEqual(foo(1), foo(1))