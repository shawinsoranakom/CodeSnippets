def test_print_hello_message(self):
        mock_is_manually_set = testutil.build_mock_config_is_manually_set(
            {"browser.serverAddress": True}
        )
        mock_get_option = testutil.build_mock_config_get_option(
            {"browser.serverAddress": "the-address"}
        )

        with patch.object(config, "get_option", new=mock_get_option), patch.object(
            config, "is_manually_set", new=mock_is_manually_set
        ):
            bootstrap._print_url(True)

        out = sys.stdout.getvalue()
        self.assertIn("Welcome to Streamlit. Check out our demo in your browser.", out)
        self.assertIn("URL: http://the-address", out)