async def test_add_multiple_git_providers_with_hosts(test_client, file_secrets_store):
    """Test adding multiple git providers with different hosts."""
    # Create initial user secrets
    user_secrets = Secrets()
    await file_secrets_store.store(user_secrets)

    # Mock check_provider_tokens to return empty string (no error)
    with patch(
        'openhands.app_server.secrets.secrets_router.check_provider_tokens',
        AsyncMock(return_value=''),
    ):
        # Add multiple providers with hosts
        add_providers_data = {
            'provider_tokens': {
                'github': {'token': 'github-token', 'host': 'github.enterprise.com'},
                'gitlab': {'token': 'gitlab-token', 'host': 'gitlab.enterprise.com'},
            }
        }
        response = test_client.post('/secrets/git-providers', json=add_providers_data)
        assert response.status_code == 200

        # Verify that both providers were stored with their respective hosts
        stored_secrets = await file_secrets_store.load()
        assert ProviderType.GITHUB in stored_secrets.provider_tokens
        assert (
            stored_secrets.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token'
        )
        assert (
            stored_secrets.provider_tokens[ProviderType.GITHUB].host
            == 'github.enterprise.com'
        )

        assert ProviderType.GITLAB in stored_secrets.provider_tokens
        assert (
            stored_secrets.provider_tokens[ProviderType.GITLAB].token.get_secret_value()
            == 'gitlab-token'
        )
        assert (
            stored_secrets.provider_tokens[ProviderType.GITLAB].host
            == 'gitlab.enterprise.com'
        )