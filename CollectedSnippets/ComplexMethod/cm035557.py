async def test_search_custom_secrets(test_client, file_secrets_store):
    """Test searching custom secrets."""
    # Create initial settings with custom secrets
    custom_secrets = {
        'API_KEY': CustomSecret(secret=SecretStr('api-key-value')),
        'DB_PASSWORD': CustomSecret(secret=SecretStr('db-password-value')),
    }
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = Secrets(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

    # Make the GET request
    response = test_client.get('/secrets/search')
    print(response)
    assert response.status_code == 200

    # Check the response
    data = response.json()
    assert 'items' in data
    # Extract just the names from the list of custom secrets
    secret_names = [secret['name'] for secret in data['items']]
    assert sorted(secret_names) == ['API_KEY', 'DB_PASSWORD']
    # Verify pagination field exists
    assert 'next_page_id' in data

    # Verify that the original settings were not modified
    stored_settings = await file_secrets_store.load()
    assert (
        stored_settings.custom_secrets['API_KEY'].secret.get_secret_value()
        == 'api-key-value'
    )
    assert (
        stored_settings.custom_secrets['DB_PASSWORD'].secret.get_secret_value()
        == 'db-password-value'
    )
    assert ProviderType.GITHUB in stored_settings.provider_tokens