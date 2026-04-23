def test_button_in_form(self):
        """Test that buttons are not allowed in forms."""

        with self.assertRaises(StreamlitAPIException) as ctx:
            with st.form("foo"):
                st.button("foo")

        self.assertIn(
            "`st.button()` can't be used in an `st.form()`", str(ctx.exception)
        )