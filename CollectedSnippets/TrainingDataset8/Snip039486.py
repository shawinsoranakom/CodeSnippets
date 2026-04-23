def test_multiple_int_like_floats(self):
        @st.cache
        def foo(x):
            return x

        self.assertEqual(foo(1.0), 1.0)
        self.assertEqual(foo(3.0), 3.0)