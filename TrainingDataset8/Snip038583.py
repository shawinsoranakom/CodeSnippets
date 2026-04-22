def test_parsing_toml(self):
        """Test config._update_config_with_toml()."""
        # Some useful variables.
        DUMMY_VAL_1, DUMMY_VAL_2 = "Christopher", "Walken"
        DUMMY_DEFINITION = "<test definition>"

        # Create a dummy default option.
        config._create_option(
            "_test.tomlTest",
            description="This option tests the TOML parser.",
            default_val=DUMMY_VAL_1,
        )
        config.get_config_options(force_reparse=True)
        self.assertEqual(config.get_option("_test.tomlTest"), DUMMY_VAL_1)
        self.assertEqual(
            config.get_where_defined("_test.tomlTest"), ConfigOption.DEFAULT_DEFINITION
        )

        # Override it with some TOML
        NEW_TOML = (
            """
            [_test]
            tomlTest="%s"
        """
            % DUMMY_VAL_2
        )
        config._update_config_with_toml(NEW_TOML, DUMMY_DEFINITION)
        self.assertEqual(config.get_option("_test.tomlTest"), DUMMY_VAL_2)
        self.assertEqual(config.get_where_defined("_test.tomlTest"), DUMMY_DEFINITION)