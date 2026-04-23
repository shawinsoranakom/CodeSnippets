def test_invalid_config_name(self):
        """Test setting an invalid config section."""
        with self.assertRaises(AssertionError):
            ConfigOption("_test.myParam.")