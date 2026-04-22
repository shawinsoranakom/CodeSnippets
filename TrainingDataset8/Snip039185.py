def test_form_in_form(self):
        """Test that forms cannot be nested in other forms."""

        with self.assertRaises(StreamlitAPIException) as ctx:
            with st.form("foo"):
                with st.form("bar"):
                    pass

        self.assertEqual(str(ctx.exception), "Forms cannot be nested in other forms.")