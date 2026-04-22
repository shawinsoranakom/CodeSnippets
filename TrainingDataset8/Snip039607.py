def test_cached(self):
        """Test decorated functions."""

        @st.cache
        def f():
            return 42

        @st.cache
        def g():
            return 12

        @st.cache
        def h():
            return 42

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertEqual(get_hash(f), get_hash(h))