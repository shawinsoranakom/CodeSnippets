def test_invalid_options(self, options, expected):
        """Test that it handles invalid options."""
        with self.assertRaises(expected):
            st.multiselect("the label", options)