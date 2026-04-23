def test_simple_config_option(self):
        """Test creating a simple (constant) config option."""
        # Create the config option.
        config_option = ConfigOption(
            "_test.simpleParam", description="Simple config option.", default_val=12345
        )

        # Test that it works.
        self.assertEqual(config_option.key, "_test.simpleParam")
        self.assertEqual(config_option.section, "_test")
        self.assertEqual(config_option.name, "simpleParam")
        self.assertEqual(config_option.description, "Simple config option.")
        self.assertEqual(config_option.where_defined, ConfigOption.DEFAULT_DEFINITION)
        self.assertEqual(config_option.value, 12345)