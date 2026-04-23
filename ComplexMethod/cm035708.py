def test_initializing_provider_tokens_with_mixed_value_types(self):
        """Test initializing provider tokens with both plain strings and SecretStr objects."""
        # Create provider tokens with mixed value types
        # Note: The ProviderToken.from_value method only accepts plain strings in the token field
        # when passed as a dictionary, not SecretStr objects
        provider_tokens_dict = {
            ProviderType.GITHUB: {
                'token': 'github-token-123',  # Plain string
                'user_id': 'user1',
            },
            ProviderType.GITLAB: {
                'token': 'gitlab-token-456',  # Also using plain string
                'user_id': 'user2',
            },
        }

        # For the second provider, create a ProviderToken directly
        gitlab_token = ProviderToken(
            token=SecretStr('gitlab-token-456'), user_id='user2'
        )

        # Create a mixed dictionary with both a dict and a ProviderToken object
        mixed_provider_tokens = {
            ProviderType.GITHUB: provider_tokens_dict[ProviderType.GITHUB],  # Dict
            ProviderType.GITLAB: gitlab_token,  # ProviderToken object
        }

        # Initialize the store
        store = Secrets(provider_tokens=mixed_provider_tokens)

        # Verify all tokens are converted to SecretStr
        assert isinstance(store.provider_tokens, MappingProxyType)
        assert len(store.provider_tokens) == 2

        # Check GitHub token (was plain string in a dict)
        github_token = store.provider_tokens[ProviderType.GITHUB]
        assert isinstance(github_token.token, SecretStr)
        assert github_token.token.get_secret_value() == 'github-token-123'
        assert github_token.user_id == 'user1'

        # Check GitLab token (was a ProviderToken object)
        gitlab_token_result = store.provider_tokens[ProviderType.GITLAB]
        assert isinstance(gitlab_token_result.token, SecretStr)
        assert gitlab_token_result.token.get_secret_value() == 'gitlab-token-456'
        assert gitlab_token_result.user_id == 'user2'