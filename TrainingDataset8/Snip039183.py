def test_multiple_forms_same_key(self):
        """Multiple forms with the same key are not allowed."""

        with self.assertRaises(StreamlitAPIException) as ctx:
            st.form(key="foo")
            st.form(key="foo")

        self.assertIn(
            "There are multiple identical forms with `key='foo'`", str(ctx.exception)
        )