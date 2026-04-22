def test_function_body_uses_nested_listcomps(self):
        @st.cache()
        def foo(arg):
            production = [[outer + inner for inner in range(3)] for outer in range(3)]
            return production

        # make sure st.cache() doesn't crash, per https://github.com/streamlit/streamlit/issues/2305
        self.assertEqual(foo(1), [[0, 1, 2], [1, 2, 3], [2, 3, 4]])