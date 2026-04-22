def test_ttl(self, timer_patch):
        """Entries should expire after the given ttl."""
        # Create 2 cached functions to test that they don't interfere
        # with each other.
        foo_vals = []

        @st.cache(ttl=1)
        def foo(x):
            foo_vals.append(x)
            return x

        bar_vals = []

        @st.cache(ttl=5)
        def bar(x):
            bar_vals.append(x)
            return x

        # Store a value at time 0
        timer_patch.return_value = 0
        foo(0)
        bar(0)
        self.assertEqual([0], foo_vals)
        self.assertEqual([0], bar_vals)

        # Advance our timer, but not enough to expire our value.
        timer_patch.return_value = 0.5
        foo(0)
        bar(0)
        self.assertEqual([0], foo_vals)
        self.assertEqual([0], bar_vals)

        # Advance our timer enough to expire foo, but not bar.
        timer_patch.return_value = 1.5
        foo(0)
        bar(0)
        self.assertEqual([0, 0], foo_vals)
        self.assertEqual([0], bar_vals)