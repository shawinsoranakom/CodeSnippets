def test_check_conflicts_server_csrf(self, get_logger):
        config._set_option("server.enableXsrfProtection", True, "test")
        config._set_option("server.enableCORS", True, "test")
        mock_logger = get_logger()
        config._check_conflicts()
        mock_logger.warning.assert_called_once()