async def test_setup_secrets_for_git_providers_descriptions_included(self):
        """Test _setup_secrets_for_git_providers includes descriptions for all provider types."""
        # Arrange
        base_secrets = {}
        self.mock_user_context.get_secrets.return_value = base_secrets
        self.mock_jwt_service.create_jws_token.return_value = 'test_access_token'

        # Mock provider tokens for multiple providers
        provider_tokens = {
            ProviderType.GITHUB: ProviderToken(token=SecretStr('github_token')),
            ProviderType.GITLAB: ProviderToken(token=SecretStr('gitlab_token')),
            ProviderType.BITBUCKET: ProviderToken(token=SecretStr('bitbucket_token')),
        }
        self.mock_user_context.get_provider_tokens = AsyncMock(
            return_value=provider_tokens
        )

        # Act
        result = await self.service._setup_secrets_for_git_providers(self.mock_user)

        # Assert - verify all secrets have correct descriptions
        assert 'GITHUB_TOKEN' in result
        assert isinstance(result['GITHUB_TOKEN'], LookupSecret)
        assert result['GITHUB_TOKEN'].description == 'GITHUB authentication token'

        assert 'GITLAB_TOKEN' in result
        assert isinstance(result['GITLAB_TOKEN'], LookupSecret)
        assert result['GITLAB_TOKEN'].description == 'GITLAB authentication token'

        assert 'BITBUCKET_TOKEN' in result
        assert isinstance(result['BITBUCKET_TOKEN'], LookupSecret)
        assert result['BITBUCKET_TOKEN'].description == 'BITBUCKET authentication token'