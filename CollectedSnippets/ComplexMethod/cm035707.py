def test_serialization_with_expose_secrets(self):
        """Test serializing the Secrets with expose_secrets=True."""
        # Create a store with both provider tokens and custom secrets
        github_token = ProviderToken(
            token=SecretStr('github-token-123'), user_id='user1'
        )
        custom_secrets = {
            'API_KEY': CustomSecret(
                secret=SecretStr('api-key-123'), description='API key'
            )
        }

        store = Secrets(
            provider_tokens=MappingProxyType({ProviderType.GITHUB: github_token}),
            custom_secrets=MappingProxyType(custom_secrets),
        )

        # Test serialization with expose_secrets=True
        serialized_provider_tokens = store.provider_tokens_serializer(
            store.provider_tokens, SerializationInfo(context={'expose_secrets': True})
        )

        serialized_custom_secrets = store.custom_secrets_serializer(
            store.custom_secrets, SerializationInfo(context={'expose_secrets': True})
        )

        # Verify provider tokens are exposed
        assert serialized_provider_tokens['github']['token'] == 'github-token-123'
        assert serialized_provider_tokens['github']['user_id'] == 'user1'

        # Verify custom secrets are exposed
        assert serialized_custom_secrets['API_KEY']['secret'] == 'api-key-123'
        assert serialized_custom_secrets['API_KEY']['description'] == 'API key'

        # Test serialization with expose_secrets=False (default)
        hidden_provider_tokens = store.provider_tokens_serializer(
            store.provider_tokens, SerializationInfo(context={'expose_secrets': False})
        )

        hidden_custom_secrets = store.custom_secrets_serializer(
            store.custom_secrets, SerializationInfo(context={'expose_secrets': False})
        )

        # Verify provider tokens are hidden
        assert hidden_provider_tokens['github']['token'] != 'github-token-123'
        assert '**' in hidden_provider_tokens['github']['token']

        # Verify custom secrets are hidden
        assert hidden_custom_secrets['API_KEY']['secret'] != 'api-key-123'
        assert '**' in hidden_custom_secrets['API_KEY']['secret']