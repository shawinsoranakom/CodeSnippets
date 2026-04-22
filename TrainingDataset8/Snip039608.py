def test_streamlit(self):
        """Test hashing streamlit functions."""

        def f():
            st.write("Hello")

        def g():
            st.write("World")

        def h():
            st.write("Hello")

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertEqual(get_hash(f), get_hash(h))