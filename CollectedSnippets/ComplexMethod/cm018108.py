async def test_enable_mfa_for_user(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test enable mfa module for user."""
    manager = await auth.auth_manager_from_config(
        hass,
        [
            {
                "type": "insecure_example",
                "users": [{"username": "test-user", "password": "test-pass"}],
            }
        ],
        [{"type": "insecure_example", "data": []}],
    )

    step = await manager.login_flow.async_init(("insecure_example", None))
    step = await manager.login_flow.async_configure(
        step["flow_id"], {"username": "test-user", "password": "test-pass"}
    )
    credential = step["result"]
    user = await manager.async_get_or_create_user(credential)
    assert user is not None

    # new user don't have mfa enabled
    modules = await manager.async_get_enabled_mfa(user)
    assert len(modules) == 0

    module = manager.get_auth_mfa_module("insecure_example")
    # mfa module don't have data
    assert bool(module._data) is False

    # test enable mfa for user
    await manager.async_enable_user_mfa(user, "insecure_example", {"pin": "test-pin"})
    assert len(module._data) == 1
    assert module._data[0] == {"user_id": user.id, "pin": "test-pin"}

    # test get enabled mfa
    modules = await manager.async_get_enabled_mfa(user)
    assert len(modules) == 1
    assert "insecure_example" in modules

    # re-enable mfa for user will override
    await manager.async_enable_user_mfa(
        user, "insecure_example", {"pin": "test-pin-new"}
    )
    assert len(module._data) == 1
    assert module._data[0] == {"user_id": user.id, "pin": "test-pin-new"}
    modules = await manager.async_get_enabled_mfa(user)
    assert len(modules) == 1
    assert "insecure_example" in modules

    # system user cannot enable mfa
    system_user = await manager.async_create_system_user("system-user")
    with pytest.raises(ValueError):
        await manager.async_enable_user_mfa(
            system_user, "insecure_example", {"pin": "test-pin"}
        )
    assert len(module._data) == 1
    modules = await manager.async_get_enabled_mfa(system_user)
    assert len(modules) == 0

    # disable mfa for user
    await manager.async_disable_user_mfa(user, "insecure_example")
    assert bool(module._data) is False

    # test get enabled mfa
    modules = await manager.async_get_enabled_mfa(user)
    assert len(modules) == 0

    # disable mfa for user don't enabled just silent fail
    await manager.async_disable_user_mfa(user, "insecure_example")