def test_convert_depecated_config_option_to_click_option(self):
        """Test that configurator_options adds extra deprecation information
        to config option's description
        """
        config_option = ConfigOption(
            "deprecated.customKey",
            description="Custom description.\n\nLine one.",
            deprecated=True,
            deprecation_text="Foo",
            expiration_date="Bar",
            type_=int,
        )

        result = _convert_config_option_to_click_option(config_option)

        self.assertEqual(
            "Custom description.\n\nLine one.\n Foo - Bar", result["description"]
        )