def test_max_size(self):
        """The oldest object should be evicted when maxsize is reached."""
        # Create 2 cached functions to test that they don't interfere
        # with each other.

        foo_vals = []

        @st.cache(max_entries=2)
        def foo(x):
            foo_vals.append(x)
            return x

        bar_vals = []

        @st.cache(max_entries=3)
        def bar(x):
            bar_vals.append(x)
            return x

        self.assertEqual([], foo_vals)
        self.assertEqual([], bar_vals)

        # Stick two items in both caches. foo will be filled.
        foo(0), foo(1)
        bar(0), bar(1)
        self.assertEqual([0, 1], foo_vals)
        self.assertEqual([0, 1], bar_vals)

        # 0, 1 are already cached, so called_values shouldn't change.
        foo(0), foo(1)
        bar(0), bar(1)
        self.assertEqual([0, 1], foo_vals)
        self.assertEqual([0, 1], bar_vals)

        # Add a new item to the cache.
        # foo: 0 should be evicted; 1 and 2 should be present.
        # bar: 0, 1, 2 present.
        foo(2)
        bar(2)

        # foo(0) again should cause 0 to be added again, since it was
        # previously evicted. Nothing will have been evicted from bar.
        foo(1), foo(0)
        bar(1), bar(0)
        self.assertEqual([0, 1, 2, 0], foo_vals)
        self.assertEqual([0, 1, 2], bar_vals)