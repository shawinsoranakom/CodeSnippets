def test_nonexistent_method(self):
        with self.assertRaises(Exception) as ctx:
            st.sidebar.non_existing()

        self.assertEqual(
            str(ctx.exception), "`non_existing()` is not a valid Streamlit command."
        )