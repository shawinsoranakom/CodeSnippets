def test_convert_config_option_to_click_option(self):
        """Test that configurator_options adds dynamic commands based on a
        config lists.
        """
        config_option = ConfigOption(
            "server.customKey",
            description="Custom description.\n\nLine one.",
            deprecated=False,
            type_=int,
        )

        result = _convert_config_option_to_click_option(config_option)

        self.assertEqual(result["option"], "--server.customKey")
        self.assertEqual(result["param"], "server_customKey")
        self.assertEqual(result["type"], config_option.type)
        self.assertEqual(result["description"], config_option.description)
        self.assertEqual(result["envvar"], "STREAMLIT_SERVER_CUSTOM_KEY")