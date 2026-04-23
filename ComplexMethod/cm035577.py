async def test_setup_secrets_for_git_providers_preserves_custom_secret_descriptions(
        self,
    ):
        """Test _setup_secrets_for_git_providers preserves descriptions from custom secrets."""
        # Arrange
        # Mock custom secrets with descriptions
        custom_secret_with_desc = StaticSecret(
            value=SecretStr('custom_secret_value'),
            description='Custom API key for external service',
        )
        custom_secret_no_desc = StaticSecret(
            value=SecretStr('another_secret_value'),
            description=None,
        )
        base_secrets = {
            'CUSTOM_API_KEY': custom_secret_with_desc,
            'ANOTHER_SECRET': custom_secret_no_desc,
        }
        self.mock_user_context.get_secrets.return_value = base_secrets
        self.mock_jwt_service.create_jws_token.return_value = 'test_access_token'

        # Mock provider tokens
        provider_tokens = {
            ProviderType.GITHUB: ProviderToken(token=SecretStr('github_token')),
        }
        self.mock_user_context.get_provider_tokens = AsyncMock(
            return_value=provider_tokens
        )

        # Act
        result = await self.service._setup_secrets_for_git_providers(self.mock_user)

        # Assert - verify custom secrets are preserved with their descriptions
        assert 'CUSTOM_API_KEY' in result
        assert isinstance(result['CUSTOM_API_KEY'], StaticSecret)
        assert (
            result['CUSTOM_API_KEY'].description
            == 'Custom API key for external service'
        )
        assert (
            result['CUSTOM_API_KEY'].value.get_secret_value() == 'custom_secret_value'
        )

        assert 'ANOTHER_SECRET' in result
        assert isinstance(result['ANOTHER_SECRET'], StaticSecret)
        assert result['ANOTHER_SECRET'].description is None
        assert (
            result['ANOTHER_SECRET'].value.get_secret_value() == 'another_secret_value'
        )

        # Verify git provider token is also included
        assert 'GITHUB_TOKEN' in result
        assert result['GITHUB_TOKEN'].description == 'GITHUB authentication token'