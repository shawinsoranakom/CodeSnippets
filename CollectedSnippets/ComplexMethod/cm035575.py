async def test_setup_secrets_for_git_providers_with_web_url(self):
        """Test _setup_secrets_for_git_providers with web URL (creates access token)."""
        # Arrange
        base_secrets = {}
        self.mock_user_context.get_secrets.return_value = base_secrets
        self.mock_jwt_service.create_jws_token.return_value = 'test_access_token'

        # Mock provider tokens
        provider_tokens = {
            ProviderType.GITHUB: ProviderToken(token=SecretStr('github_token')),
            ProviderType.GITLAB: ProviderToken(token=SecretStr('gitlab_token')),
        }
        self.mock_user_context.get_provider_tokens = AsyncMock(
            return_value=provider_tokens
        )

        # Act
        result = await self.service._setup_secrets_for_git_providers(self.mock_user)

        # Assert
        assert 'GITHUB_TOKEN' in result
        assert 'GITLAB_TOKEN' in result
        assert isinstance(result['GITHUB_TOKEN'], LookupSecret)
        assert isinstance(result['GITLAB_TOKEN'], LookupSecret)
        assert (
            result['GITHUB_TOKEN'].url
            == 'https://test.example.com/api/v1/webhooks/secrets'
        )
        assert result['GITHUB_TOKEN'].headers['X-Access-Token'] == 'test_access_token'
        # Verify descriptions are included
        assert result['GITHUB_TOKEN'].description == 'GITHUB authentication token'
        assert result['GITLAB_TOKEN'].description == 'GITLAB authentication token'

        # Should be called twice, once for each provider
        assert self.mock_jwt_service.create_jws_token.call_count == 2