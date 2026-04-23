async def test_add_multiple_custom_secrets(test_client, file_secrets_store):
    """Test adding multiple custom secrets at once."""
    # Create initial settings with one custom secret
    custom_secrets = {
        'EXISTING_SECRET': CustomSecret(secret=SecretStr('existing-value'))
    }
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = Secrets(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

    # Make the POST request to add first custom secret
    add_secret_data1 = {
        'name': 'API_KEY',
        'value': 'api-key-value',
        'description': None,
    }
    response1 = test_client.post('/secrets', json=add_secret_data1)
    assert response1.status_code == 201

    # Make the POST request to add second custom secret
    add_secret_data2 = {
        'name': 'DB_PASSWORD',
        'value': 'db-password-value',
        'description': None,
    }
    response = test_client.post('/secrets', json=add_secret_data2)
    assert response.status_code == 201

    # Verify that the settings were stored with the new secrets
    stored_settings = await file_secrets_store.load()

    # Check that the new secrets were added
    assert 'API_KEY' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['API_KEY'].secret.get_secret_value()
        == 'api-key-value'
    )
    assert 'DB_PASSWORD' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['DB_PASSWORD'].secret.get_secret_value()
        == 'db-password-value'
    )

    # Check that existing secrets were preserved
    assert 'EXISTING_SECRET' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['EXISTING_SECRET'].secret.get_secret_value()
        == 'existing-value'
    )

    # Check that other settings were preserved
    assert ProviderType.GITHUB in stored_settings.provider_tokens