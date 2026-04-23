async def test_login_as_existing_user(mock_hass) -> None:
    """Test login as existing user."""
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
                    }
                ],
            }
        ],
        [],
    )
    mock_hass.auth = manager
    ensure_auth_manager_loaded(manager)

    # Add a fake user that we're not going to log in with
    user = MockUser(
        id="mock-user2", is_owner=False, is_active=False, name="Not user"
    ).add_to_auth_manager(manager)
    user.credentials.append(
        auth_models.Credentials(
            id="mock-id2",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "other-user"},
            is_new=False,
        )
    )

    # Add fake user with credentials for example auth provider.
    user = MockUser(
        id="mock-user", is_owner=False, is_active=False, name="Paulus"
    ).add_to_auth_manager(manager)
    user.credentials.append(
        auth_models.Credentials(
            id="mock-id",
            auth_provider_type="insecure_example",
            auth_provider_id=None,
            data={"username": "test-user"},
            is_new=False,
        )
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    assert step["type"] == data_entry_flow.FlowResultType.FORM

    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    assert step["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

    credential = step["result"]
    user = await manager.async_get_user_by_credentials(credential)
    assert user is not None
    assert user.id == "mock-user"
    assert user.is_owner is False
    assert user.is_active is False
    assert user.name == "Paulus"