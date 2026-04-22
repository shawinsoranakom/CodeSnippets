def test_print_urls_local(self, mock_get_internal_ip):
        mock_is_manually_set = testutil.build_mock_config_is_manually_set(
            {"browser.serverAddress": False}
        )
        mock_get_option = testutil.build_mock_config_get_option(
            {"server.headless": False}
        )

        mock_get_internal_ip.return_value = "internal-ip"

        with patch.object(config, "get_option", new=mock_get_option), patch.object(
            config, "is_manually_set", new=mock_is_manually_set
        ):
            bootstrap._print_url(False)

        out = sys.stdout.getvalue()
        self.assertIn("Local URL: http://localhost", out)
        self.assertIn("Network URL: http://internal-ip", out)