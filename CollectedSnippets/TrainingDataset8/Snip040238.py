def test_log_secret_load_error(self, mock_load_secrets, mock_log_error):
        """If secrets throws an error on startup, we catch and log it."""
        mock_exception = Exception("Secrets exploded!")
        mock_load_secrets.side_effect = mock_exception

        bootstrap._on_server_start(Mock())
        mock_log_error.assert_called_once_with(
            "Failed to load secrets.toml file",
            exc_info=mock_exception,
        )