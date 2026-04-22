def test_unknown_arguments(self):
        """Test st.write that raises an exception."""
        with self.assertLogs(write._LOGGER) as logs:
            st.write("some text", unknown_keyword_arg=123)

        self.assertIn(
            'Invalid arguments were passed to "st.write" function.', logs.records[0].msg
        )