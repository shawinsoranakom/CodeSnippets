def test_no_max_size(self):
        """If max_size is None, the cache is unbounded."""
        called_values = []

        @st.cache(max_entries=None)
        def f(x):
            called_values.append(x)
            return x

        # Stick a bunch of items in the cache.
        for ii in range(256):
            f(ii)

        # Clear called_values, and test that accessing the same bunch of
        # items doesn't result in f() being called.
        called_values = []
        for ii in range(256):
            f(ii)
        self.assertEqual([], called_values)