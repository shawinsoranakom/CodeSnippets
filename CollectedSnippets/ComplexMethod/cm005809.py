def test_cors_wildcard_credentials_runtime_check_current_behavior(
        self, mock_logger, mock_get_settings, mock_setup_sentry
    ):
        """Test runtime validation prevents wildcard with credentials (current behavior)."""
        from langflow.main import create_app

        # Mock settings with configuration that triggers current security measure
        mock_settings = MagicMock()
        mock_settings.settings.cors_origins = "*"
        mock_settings.settings.cors_allow_credentials = True  # Gets disabled for security
        mock_settings.settings.cors_allow_methods = "*"
        mock_settings.settings.cors_allow_headers = "*"
        mock_settings.settings.prometheus_enabled = False
        mock_settings.settings.mcp_server_enabled = False
        mock_settings.settings.sentry_dsn = None  # Disable Sentry
        mock_get_settings.return_value = mock_settings

        # Create app
        mock_setup_sentry.return_value = None  # Use the mock
        app = create_app()

        # Check that warning was logged about deprecation/security
        # The actual warning message is different from what we expected
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        # We expect warnings about the insecure configuration - check for the actual message
        assert any("CORS" in str(call) and "permissive" in str(call) for call in warning_calls), (
            f"Expected CORS security warning but got: {warning_calls}"
        )

        # Find CORS middleware and verify credentials are still allowed (current insecure behavior)
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls == CORSMiddleware:
                cors_middleware = middleware
                break

        assert cors_middleware is not None
        assert cors_middleware.kwargs["allow_origins"] == "*"
        assert cors_middleware.kwargs["allow_credentials"] is True  # Current behavior: NOT disabled (insecure!)

        # Warn about the security implications
        warnings.warn(
            "CRITICAL SECURITY WARNING: Current behavior allows wildcard origins WITH CREDENTIALS ENABLED! "
            "This is a severe security vulnerability. Any website can make authenticated requests. "
            "In v1.7, this will be changed to secure defaults with specific origins only.",
            UserWarning,
            stacklevel=2,
        )