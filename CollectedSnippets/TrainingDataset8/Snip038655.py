def test_sidebar_nonexistent_method(self):
        with self.assertRaises(Exception) as ctx:
            st.sidebar.echo()

        self.assertEqual(
            str(ctx.exception),
            "Method `echo()` does not exist for `st.sidebar`. "
            "Did you mean `st.echo()`?",
        )