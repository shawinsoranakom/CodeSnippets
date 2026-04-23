def test_model_copy_update_fields(self):
        """Test using model_copy to update fields without affecting other fields."""
        # Create initial store
        github_token = ProviderToken(
            token=SecretStr('github-token-123'), user_id='user1'
        )
        custom_secret = {
            'API_KEY': CustomSecret(
                secret=SecretStr('api-key-123'), description='API key'
            )
        }

        initial_store = Secrets(
            provider_tokens=MappingProxyType({ProviderType.GITHUB: github_token}),
            custom_secrets=MappingProxyType(custom_secret),
        )

        # Update only provider_tokens
        gitlab_token = ProviderToken(
            token=SecretStr('gitlab-token-456'), user_id='user2'
        )
        updated_provider_tokens = MappingProxyType(
            {ProviderType.GITHUB: github_token, ProviderType.GITLAB: gitlab_token}
        )

        updated_store1 = initial_store.model_copy(
            update={'provider_tokens': updated_provider_tokens}
        )

        # Verify provider_tokens was updated but custom_secrets remains the same
        assert len(updated_store1.provider_tokens) == 2
        assert (
            updated_store1.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token-123'
        )
        assert (
            updated_store1.provider_tokens[ProviderType.GITLAB].token.get_secret_value()
            == 'gitlab-token-456'
        )
        assert len(updated_store1.custom_secrets) == 1
        assert (
            updated_store1.custom_secrets['API_KEY'].secret.get_secret_value()
            == 'api-key-123'
        )

        # Update only custom_secrets
        updated_custom_secrets = MappingProxyType(
            {
                'API_KEY': CustomSecret(
                    secret=SecretStr('api-key-123'), description='API key'
                ),
                'DATABASE_PASSWORD': CustomSecret(
                    secret=SecretStr('db-pass-456'), description='DB password'
                ),
            }
        )

        updated_store2 = initial_store.model_copy(
            update={'custom_secrets': updated_custom_secrets}
        )

        # Verify custom_secrets was updated but provider_tokens remains the same
        assert len(updated_store2.provider_tokens) == 1
        assert (
            updated_store2.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token-123'
        )
        assert len(updated_store2.custom_secrets) == 2
        assert (
            updated_store2.custom_secrets['API_KEY'].secret.get_secret_value()
            == 'api-key-123'
        )
        assert (
            updated_store2.custom_secrets['DATABASE_PASSWORD'].secret.get_secret_value()
            == 'db-pass-456'
        )