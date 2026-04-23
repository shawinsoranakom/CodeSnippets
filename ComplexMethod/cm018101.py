async def test_saving_loading(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test storing and saving data.

    Creates one of each type that we store to test we restore correctly.
    """
    manager = await auth.auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [{"username": "test-user", "password": "test-pass"}],
            }
        ],
        [],
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    credential = step["result"]
    user = await manager.async_get_or_create_user(credential)

    await manager.async_activate_user(user)
    # the first refresh token will be used to create access token
    refresh_token = await manager.async_create_refresh_token(
        user, CLIENT_ID, credential=credential
    )
    manager.async_create_access_token(refresh_token, "192.168.0.1")
    # the second refresh token will not be used
    await manager.async_create_refresh_token(
        user, "dummy-client", credential=credential
    )

    await flush_store(manager._store._store)

    store2 = auth_store.AuthStore(hass)
    await store2.async_load()
    users = await store2.async_get_users()
    assert len(users) == 1
    assert users[0].permissions == user.permissions
    assert users[0] == user
    assert len(users[0].refresh_tokens) == 2
    for r_token in users[0].refresh_tokens.values():
        if r_token.client_id == CLIENT_ID:
            # verify the first refresh token
            assert r_token.last_used_at is not None
            assert r_token.last_used_ip == "192.168.0.1"
        elif r_token.client_id == "dummy-client":
            # verify the second refresh token
            assert r_token.last_used_at is None
            assert r_token.last_used_ip is None
        else:
            pytest.fail(f"Unknown client_id: {r_token.client_id}")