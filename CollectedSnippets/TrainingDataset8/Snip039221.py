def test_only_label_strings_allowed(self):
        """Test that only strings are allowed as tab labels."""
        with self.assertRaises(StreamlitAPIException):
            st.tabs(["tab1", True])

        with self.assertRaises(StreamlitAPIException):
            st.tabs(["tab1", 10])