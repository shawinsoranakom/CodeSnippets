def test_load_secrets(self, mock_load_secrets):
        """We should load secrets.toml on startup."""
        bootstrap._on_server_start(Mock())
        mock_load_secrets.assert_called_once()