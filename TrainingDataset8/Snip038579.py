def test_cannot_overwrite_config_section(self):
        """Test overwriting a config section using _create_section."""
        with self.assertRaises(AssertionError):
            config._create_section("_test2", "A test section.")
            config._create_section("_test2", "A test section.")