def test_none_args(self):
        """Test that an error is raised when called with args set to None."""
        with self.assertRaises(ValueError):
            st._legacy_vega_lite_chart(None, None)