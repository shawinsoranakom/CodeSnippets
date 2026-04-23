async def test_trusted_users_login(
    manager_with_user: auth.AuthManager,
    provider_with_user: tn_auth.TrustedNetworksAuthProvider,
) -> None:
    """Test available user list changed per different IP."""
    owner = await manager_with_user.async_create_user("test-owner")
    sys_user = await manager_with_user.async_create_system_user(
        "test-sys-user"
    )  # system user will not be available to select
    user = await manager_with_user.async_create_user("test-user")

    # change the trusted users config
    config = provider_with_user.config["trusted_users"]
    assert ip_network("192.168.0.1") in config
    config[ip_network("192.168.0.1")] = [owner.id]
    assert ip_network("192.168.128.0/24") in config
    config[ip_network("192.168.128.0/24")] = [sys_user.id, user.id]

    # not from trusted network
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("127.0.0.1")}
    )
    step = await flow.async_step_init()
    assert step["type"] is FlowResultType.ABORT
    assert step["reason"] == "not_allowed"

    # from trusted network, list users intersect trusted_users
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("192.168.0.1")}
    )
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    # only owner listed
    assert schema({"user": owner.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": user.id})

    # from trusted network, list users intersect trusted_users
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("192.168.128.1")}
    )
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    # only user listed
    assert schema({"user": user.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": owner.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": sys_user.id})

    # from trusted network, list users intersect trusted_users
    flow = await provider_with_user.async_login_flow({"ip_address": ip_address("::1")})
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    # both owner and user listed
    assert schema({"user": owner.id})
    assert schema({"user": user.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": sys_user.id})

    # from trusted network, list users intersect trusted_users
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("fd00::1")}
    )
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    # no user listed
    with pytest.raises(vol.Invalid):
        assert schema({"user": owner.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": user.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": sys_user.id})