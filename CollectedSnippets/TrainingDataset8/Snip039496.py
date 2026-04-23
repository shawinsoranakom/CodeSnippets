def test_unique_function_caches(self):
        """Each function should have its own cache, even if it has an
        identical body and arguments to another cached function.
        """

        @st.cache
        def foo():
            return []

        @st.cache
        def bar():
            return []

        id_foo = id(foo())
        id_bar = id(bar())
        self.assertNotEqual(id_foo, id_bar)