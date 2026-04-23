def test_hello_command_with_logs(self, get_logger):
        """Tests setting log level using --log_level prints a warning."""

        with patch("streamlit.web.cli._main_run"):
            self.runner.invoke(cli, ["--log_level", "error", "hello"])

            mock_logger = get_logger()
            mock_logger.warning.assert_called_once()