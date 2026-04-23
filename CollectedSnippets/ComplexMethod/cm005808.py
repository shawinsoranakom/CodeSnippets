def test_cors_middleware_configuration(self, mock_get_settings, mock_setup_sentry):
        """Test that CORS middleware is configured correctly in the app."""
        from langflow.main import create_app

        # Mock settings
        mock_settings = MagicMock()
        mock_settings.settings.cors_origins = ["https://app.example.com"]
        mock_settings.settings.cors_allow_credentials = True
        mock_settings.settings.cors_allow_methods = ["GET", "POST"]
        mock_settings.settings.cors_allow_headers = ["Content-Type"]
        mock_settings.settings.prometheus_enabled = False
        mock_settings.settings.mcp_server_enabled = False
        mock_settings.settings.sentry_dsn = None  # Disable Sentry
        mock_get_settings.return_value = mock_settings

        # Create app
        mock_setup_sentry.return_value = None  # Use the mock
        app = create_app()

        # Find CORS middleware
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls == CORSMiddleware:
                cors_middleware = middleware
                break

        assert cors_middleware is not None
        assert cors_middleware.kwargs["allow_origins"] == ["https://app.example.com"]
        assert cors_middleware.kwargs["allow_credentials"] is True
        assert cors_middleware.kwargs["allow_methods"] == ["GET", "POST"]
        assert cors_middleware.kwargs["allow_headers"] == ["Content-Type"]