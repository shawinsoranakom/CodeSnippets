async def test_get_user(forgejo_service):
    # Mock response data
    mock_user_data = {
        'id': 1,
        'username': 'test_user',
        'avatar_url': 'https://codeberg.org/avatar/test_user',
        'full_name': 'Test User',
        'email': 'test@example.com',
        'organization': 'Test Org',
    }

    # Mock the _make_request method
    forgejo_service._make_request = AsyncMock(return_value=(mock_user_data, {}))

    # Call the method
    user = await forgejo_service.get_user()

    # Verify the result
    assert isinstance(user, User)
    assert user.id == '1'
    assert user.login == 'test_user'
    assert user.avatar_url == 'https://codeberg.org/avatar/test_user'
    assert user.name == 'Test User'
    assert user.email == 'test@example.com'
    assert user.company == 'Test Org'

    # Verify the _fetch_data call
    forgejo_service._make_request.assert_called_once_with(
        f'{forgejo_service.BASE_URL}/user'
    )