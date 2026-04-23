def test_invalid_config_section(self):
        """Test setting an invalid config section."""
        with self.assertRaises(AssertionError):
            config._create_option("mySection.myParam")