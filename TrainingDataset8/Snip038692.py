def test_progress_bad_values(self):
        """Test Progress with bad values."""
        values = [-1, 101, -0.01, 1.01]
        for value in values:
            with self.assertRaises(StreamlitAPIException):
                st.progress(value)

        with self.assertRaises(StreamlitAPIException):
            st.progress("some string")