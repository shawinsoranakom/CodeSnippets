def test_initializing_with_mixed_types(self):
        """Test initializing the store with mixed types (dict and MappingProxyType)."""
        # Create provider tokens as a dict
        provider_tokens_dict = {
            ProviderType.GITHUB: {'token': 'github-token-123', 'user_id': 'user1'},
        }

        # Create custom secrets as a MappingProxyType
        custom_secret = CustomSecret(
            secret=SecretStr('api-key-123'), description='API key'
        )
        custom_secrets_proxy = MappingProxyType({'API_KEY': custom_secret})

        # Test with dict for provider_tokens and MappingProxyType for custom_secrets
        store1 = Secrets(
            provider_tokens=provider_tokens_dict, custom_secrets=custom_secrets_proxy
        )

        assert isinstance(store1.provider_tokens, MappingProxyType)
        assert isinstance(store1.custom_secrets, MappingProxyType)
        assert (
            store1.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token-123'
        )
        assert (
            store1.custom_secrets['API_KEY'].secret.get_secret_value() == 'api-key-123'
        )

        # Test with MappingProxyType for provider_tokens and dict for custom_secrets
        provider_token = ProviderToken(
            token=SecretStr('gitlab-token-456'), user_id='user2'
        )
        provider_tokens_proxy = MappingProxyType({ProviderType.GITLAB: provider_token})

        # Create custom secrets as a dict
        custom_secrets_dict = {
            'API_KEY': {'secret': 'api-key-123', 'description': 'API key'}
        }

        store2 = Secrets(
            provider_tokens=provider_tokens_proxy, custom_secrets=custom_secrets_dict
        )

        assert isinstance(store2.provider_tokens, MappingProxyType)
        assert isinstance(store2.custom_secrets, MappingProxyType)
        assert (
            store2.provider_tokens[ProviderType.GITLAB].token.get_secret_value()
            == 'gitlab-token-456'
        )
        assert (
            store2.custom_secrets['API_KEY'].secret.get_secret_value() == 'api-key-123'
        )