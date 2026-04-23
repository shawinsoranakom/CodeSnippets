def test_clear_cache(self):
        """Clear cache should do its thing."""
        foo_vals = []

        @st.cache
        def foo(x):
            foo_vals.append(x)
            return x

        bar_vals = []

        @st.cache
        def bar(x):
            bar_vals.append(x)
            return x

        foo(0), foo(1), foo(2)
        bar(0), bar(1), bar(2)
        self.assertEqual([0, 1, 2], foo_vals)
        self.assertEqual([0, 1, 2], bar_vals)

        # Clear the cache and access our original values again. They
        # should be recomputed.
        caching.clear_cache()

        foo(0), foo(1), foo(2)
        bar(0), bar(1), bar(2)
        self.assertEqual([0, 1, 2, 0, 1, 2], foo_vals)
        self.assertEqual([0, 1, 2, 0, 1, 2], bar_vals)