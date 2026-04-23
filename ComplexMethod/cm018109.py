async def test_new_users(mock_hass) -> None:
    """Test newly created users."""
    manager = await auth.auth_manager_from_config(
        mock_hass,
        [
            {
                "type": "insecure_example",
                "users": [
                    {
                        "username": "test-user",
                        "password": "test-pass",
                        "name": "Test Name",
                    },
                    {
                        "username": "test-user-2",
                        "password": "test-pass",
                        "name": "Test Name",
                    },
                    {
                        "username": "test-user-3",
                        "password": "test-pass",
                        "name": "Test Name",
                    },
                ],
            }
        ],
        [],
    )
    ensure_auth_manager_loaded(manager)

    user = await manager.async_create_user("Hello")
    # first user in the system is owner and admin
    assert user.is_owner
    assert user.is_admin
    assert not user.local_only
    assert user.groups == []

    user = await manager.async_create_user("Hello 2")
    assert not user.is_admin
    assert user.groups == []

    user = await manager.async_create_user(
        "Hello 3", group_ids=["system-admin"], local_only=True
    )
    assert user.is_admin
    assert user.groups[0].id == "system-admin"
    assert user.local_only

    user_cred = await manager.async_get_or_create_user(
        auth_models.Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=True,
        )
    )
    assert user_cred.is_admin