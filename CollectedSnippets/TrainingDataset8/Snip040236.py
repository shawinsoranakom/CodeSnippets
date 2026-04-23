def test_load_config_options(self, patched_get_config_options):
        """Test that bootstrap.load_config_options parses the keys properly and
        passes down the parameters.
        """

        flag_options = {
            "server_port": 3005,
            "server_headless": True,
            "browser_serverAddress": "localhost",
            "logger_level": "error",
            # global_minCachedMessageSize shouldn't be set below since it's None.
            "global_minCachedMessageSize": None,
        }

        bootstrap.load_config_options(flag_options)

        patched_get_config_options.assert_called_once_with(
            force_reparse=True,
            options_from_flags={
                "server.port": 3005,
                "server.headless": True,
                "browser.serverAddress": "localhost",
                "logger.level": "error",
            },
        )