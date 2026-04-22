def test_ttl(self, timer_patch):
        """Entries should expire after the given ttl."""
        one_day = 60 * 60 * 24

        # Create 2 cached functions to test that they don't interfere
        # with each other.
        foo_vals = []

        @st.experimental_memo(ttl=one_day)
        def foo(x):
            foo_vals.append(x)
            return x

        bar_vals = []

        @st.experimental_memo(ttl=one_day * 2)
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
        timer_patch.return_value = one_day * 0.5
        foo(0)
        bar(0)
        self.assertEqual([0], foo_vals)
        self.assertEqual([0], bar_vals)

        # Advance our timer enough to expire foo, but not bar.
        timer_patch.return_value = one_day * 1.5
        foo(0)
        bar(0)
        self.assertEqual([0, 0], foo_vals)
        self.assertEqual([0], bar_vals)

        # Expire bar. Foo's second value was inserted at time=1.5 days,
        # so it won't expire until time=2.5 days
        timer_patch.return_value = (one_day * 2) + 1
        foo(0)
        bar(0)
        self.assertEqual([0, 0], foo_vals)
        self.assertEqual([0, 0], bar_vals)

        # Expire foo for a second time.
        timer_patch.return_value = (one_day * 2.5) + 1
        foo(0)
        bar(0)
        self.assertEqual([0, 0, 0], foo_vals)
        self.assertEqual([0, 0], bar_vals)