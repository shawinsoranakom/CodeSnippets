async def test_trusted_group_login(
    manager_with_user: auth.AuthManager,
    provider_with_user: tn_auth.TrustedNetworksAuthProvider,
) -> None:
    """Test config trusted_user with group_id."""
    owner = await manager_with_user.async_create_user("test-owner")
    # create a user in user group
    user = await manager_with_user.async_create_user("test-user")
    await manager_with_user.async_update_user(
        user, group_ids=[auth.const.GROUP_ID_USER]
    )

    # change the trusted users config
    config = provider_with_user.config["trusted_users"]
    assert ip_network("192.168.0.1") in config
    config[ip_network("192.168.0.1")] = [{"group": [auth.const.GROUP_ID_USER]}]
    assert ip_network("192.168.128.0/24") in config
    config[ip_network("192.168.128.0/24")] = [
        owner.id,
        {"group": [auth.const.GROUP_ID_USER]},
    ]

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
    # only user listed
    assert schema({"user": user.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": owner.id})

    # from trusted network, list users intersect trusted_users
    flow = await provider_with_user.async_login_flow(
        {"ip_address": ip_address("192.168.128.1")}
    )
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    # both owner and user listed
    assert schema({"user": owner.id})
    assert schema({"user": user.id})