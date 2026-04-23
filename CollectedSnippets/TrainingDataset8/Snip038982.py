def test_invalid_defaults(self, defaults, expected):
        """Test that invalid default trigger the expected exception."""
        with self.assertRaises(expected):
            st.multiselect("the label", ["Coffee", "Tea", "Water"], defaults)