def test_hello_command_with_flag_config_options(self):
        with patch("validators.url", return_value=False), patch(
            "streamlit.web.cli._main_run"
        ), patch("os.path.exists", return_value=True):

            result = self.runner.invoke(cli, ["hello", "--server.port=8502"])

        streamlit.web.bootstrap.load_config_options.assert_called_once()
        _args, kwargs = streamlit.web.bootstrap.load_config_options.call_args
        self.assertEqual(kwargs["flag_options"]["server_port"], 8502)
        self.assertEqual(0, result.exit_code)