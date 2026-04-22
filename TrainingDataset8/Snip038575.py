def test_complex_config_option(self):
        """Test setting a complex (functional) config option."""
        # Create the config option.
        @ConfigOption("_test.complexParam")
        def config_option():
            """Complex config option."""
            return 12345

        # Test that it works.
        self.assertEqual(config_option.key, "_test.complexParam")
        self.assertEqual(config_option.section, "_test")
        self.assertEqual(config_option.name, "complexParam")
        self.assertEqual(config_option.description, "Complex config option.")
        self.assertEqual(config_option.where_defined, ConfigOption.DEFAULT_DEFINITION)
        self.assertEqual(config_option.value, 12345)