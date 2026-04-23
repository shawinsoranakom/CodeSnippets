async def test_search_custom_secrets_pagination(test_client, file_secrets_store):
    """Test searching custom secrets with pagination."""
    # Create initial settings with many custom secrets
    custom_secrets = {
        f'SECRET_{i:02d}': CustomSecret(secret=SecretStr(f'value-{i}'))
        for i in range(5)
    }
    user_secrets = Secrets(custom_secrets=custom_secrets)

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

    # Make the first GET request with limit
    response = test_client.get('/secrets/search', params={'limit': 2})
    assert response.status_code == 200

    # Check the response
    data = response.json()
    assert 'items' in data
    assert len(data['items']) == 2
    # Results should be sorted alphabetically
    assert data['items'][0]['name'] == 'SECRET_00'
    assert data['items'][1]['name'] == 'SECRET_01'
    # Since there are more items, next_page_id should be set
    assert data['next_page_id'] == 'SECRET_01'

    # Make the second GET request with page_id
    response = test_client.get(
        '/secrets/search', params={'limit': 2, 'page_id': data['next_page_id']}
    )
    assert response.status_code == 200

    # Check the response
    data = response.json()
    assert len(data['items']) == 2
    assert data['items'][0]['name'] == 'SECRET_02'
    assert data['items'][1]['name'] == 'SECRET_03'