def test_adding_only_provider_tokens(self):
        """Test adding only provider tokens to the Secrets."""
        # Create provider tokens
        github_token = ProviderToken(
            token=SecretStr('github-token-123'), user_id='user1'
        )
        gitlab_token = ProviderToken(
            token=SecretStr('gitlab-token-456'), user_id='user2'
        )

        # Create a store with only provider tokens
        provider_tokens = {
            ProviderType.GITHUB: github_token,
            ProviderType.GITLAB: gitlab_token,
        }

        # Initialize the store with a dict that will be converted to MappingProxyType
        store = Secrets(provider_tokens=provider_tokens)

        # Verify the tokens were added correctly
        assert isinstance(store.provider_tokens, MappingProxyType)
        assert len(store.provider_tokens) == 2
        assert (
            store.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token-123'
        )
        assert store.provider_tokens[ProviderType.GITHUB].user_id == 'user1'
        assert (
            store.provider_tokens[ProviderType.GITLAB].token.get_secret_value()
            == 'gitlab-token-456'
        )
        assert store.provider_tokens[ProviderType.GITLAB].user_id == 'user2'

        # Verify custom_secrets is empty
        assert isinstance(store.custom_secrets, MappingProxyType)
        assert len(store.custom_secrets) == 0