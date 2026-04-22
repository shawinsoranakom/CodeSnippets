def test_no_args(self):
        """Test that an error is raised when called with no args."""
        with self.assertRaises(ValueError):
            st._legacy_vega_lite_chart()