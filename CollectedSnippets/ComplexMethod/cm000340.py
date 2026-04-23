def test_provider_builder_complete_example(self):
        """Test building a complete provider with all features."""
        from backend.blocks._base import BlockCostType

        class TestOAuth(BaseOAuthHandler):
            PROVIDER_NAME = ProviderName.GITHUB

        class TestWebhook(BaseWebhooksManager):
            PROVIDER_NAME = ProviderName.GITHUB

        def client_factory():
            return Mock()

        def error_handler(exc):
            return str(exc)

        # Set environment variables for OAuth to be registered
        with patch.dict(
            os.environ,
            {
                "COMPLETE_TEST_CLIENT_ID": "test_id",
                "COMPLETE_TEST_CLIENT_SECRET": "test_secret",
                "COMPLETE_API_KEY": "test_api_key",
            },
        ):
            provider = (
                ProviderBuilder("complete_test")
                .with_api_key("COMPLETE_API_KEY", "Complete API Key")
                .with_oauth(TestOAuth, scopes=["read"])
                .with_webhook_manager(TestWebhook)
                .with_base_cost(100, BlockCostType.RUN)
                .with_api_client(client_factory)
                .with_error_handler(error_handler)
                .with_config(custom_setting="value")
                .build()
            )

            # Verify all settings
            assert provider.name == "complete_test"
            assert "api_key" in provider.supported_auth_types
            assert "oauth2" in provider.supported_auth_types
            assert provider.oauth_config is not None
            assert provider.oauth_config.oauth_handler == TestOAuth
            assert provider.webhook_manager == TestWebhook
            assert len(provider.base_costs) == 1
            assert provider._api_client_factory == client_factory
            assert provider._error_handler == error_handler
            assert provider.get_config("custom_setting") == "value"  # from with_config

            # Verify it's registered
            assert AutoRegistry.get_provider("complete_test") == provider
            assert "complete_test" in AutoRegistry._oauth_handlers
            assert "complete_test" in AutoRegistry._webhook_managers