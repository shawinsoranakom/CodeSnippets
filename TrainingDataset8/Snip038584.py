def test_parsing_env_vars_in_toml(self):
        """Test that environment variables get parsed in the TOML file."""
        # Some useful variables.
        DEFAULT_VAL, DESIRED_VAL = "Christopher", "Walken"
        DUMMY_DEFINITION = "<test definition>"

        # Create a dummy default option.
        config._create_option(
            "_test.tomlTest",
            description="This option tests the TOML parser.",
            default_val=DEFAULT_VAL,
        )
        config.get_config_options(force_reparse=True)
        self.assertEqual(config.get_option("_test.tomlTest"), DEFAULT_VAL)
        self.assertEqual(
            config.get_where_defined("_test.tomlTest"), ConfigOption.DEFAULT_DEFINITION
        )

        os.environ["TEST_ENV_VAR"] = DESIRED_VAL

        # Override it with some TOML
        NEW_TOML = """
            [_test]
            tomlTest="env:TEST_ENV_VAR"
        """
        config._update_config_with_toml(NEW_TOML, DUMMY_DEFINITION)
        self.assertEqual(config.get_option("_test.tomlTest"), DESIRED_VAL)
        self.assertEqual(config.get_where_defined("_test.tomlTest"), DUMMY_DEFINITION)