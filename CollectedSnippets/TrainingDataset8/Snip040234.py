def test_print_socket(self):
        mock_is_manually_set = testutil.build_mock_config_is_manually_set(
            {"browser.serverAddress": False}
        )

        mock_get_option = testutil.build_mock_config_get_option(
            {
                "server.address": "unix://mysocket.sock",
                "global.developmentMode": False,
            }
        )

        with patch.object(config, "get_option", new=mock_get_option), patch.object(
            config, "is_manually_set", new=mock_is_manually_set
        ):
            bootstrap._print_url(False)

        out = sys.stdout.getvalue()
        self.assertIn("Unix Socket: unix://mysocket.sock", out)