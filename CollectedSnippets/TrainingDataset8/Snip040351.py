def test_get_url(
        self, base_url: Optional[str], port: Optional[int], expected_url: str
    ):
        options = {"server.headless": False, "global.developmentMode": False}

        if base_url:
            options["server.baseUrlPath"] = base_url

        if port:
            options["server.port"] = port

        mock_get_option = testutil.build_mock_config_get_option(options)

        with patch.object(config, "get_option", new=mock_get_option):
            actual_url = server_util.get_url("the_ip_address")

        self.assertEqual(expected_url, actual_url)