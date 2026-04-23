async def test_login_flow(
    manager: auth.AuthManager, provider: tn_auth.TrustedNetworksAuthProvider
) -> None:
    """Test login flow."""
    owner = await manager.async_create_user("test-owner")
    user = await manager.async_create_user("test-user")

    # not from trusted network
    flow = await provider.async_login_flow({"ip_address": ip_address("127.0.0.1")})
    step = await flow.async_step_init()
    assert step["type"] is FlowResultType.ABORT
    assert step["reason"] == "not_allowed"

    # from trusted network, list users
    flow = await provider.async_login_flow({"ip_address": ip_address("192.168.0.1")})
    step = await flow.async_step_init()
    assert step["step_id"] == "init"

    schema = step["data_schema"]
    assert schema({"user": owner.id})
    with pytest.raises(vol.Invalid):
        assert schema({"user": "invalid-user"})

    # login with valid user
    step = await flow.async_step_init({"user": user.id})
    assert step["type"] is FlowResultType.CREATE_ENTRY
    assert step["data"]["user"] == user.id