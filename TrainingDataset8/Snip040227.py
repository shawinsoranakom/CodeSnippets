def test_print_urls_remote(self, mock_get_internal_ip, mock_get_external_ip):
        mock_is_manually_set = testutil.build_mock_config_is_manually_set(
            {"browser.serverAddress": False}
        )
        mock_get_option = testutil.build_mock_config_get_option(
            {"server.headless": True}
        )

        mock_get_internal_ip.return_value = "internal-ip"
        mock_get_external_ip.return_value = "external-ip"

        with patch.object(config, "get_option", new=mock_get_option), patch.object(
            config, "is_manually_set", new=mock_is_manually_set
        ):
            bootstrap._print_url(False)

        out = sys.stdout.getvalue()
        self.assertIn("Network URL: http://internal-ip", out)
        self.assertIn("External URL: http://external-ip", out)