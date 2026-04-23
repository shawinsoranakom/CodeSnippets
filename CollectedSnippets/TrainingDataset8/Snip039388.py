def test_function_not_hashable(self):
        def foo():
            pass

        with self.assertRaises(UnhashableTypeError):
            get_hash(foo)