async def test_login_flow_validates(data: hass_auth.Data, hass: HomeAssistant) -> None:
    """Test login flow."""
    data.add_auth("test-user", "test-pass")
    await data.async_save()

    provider = hass_auth.HassAuthProvider(
        hass, auth_store.AuthStore(hass), {"type": "homeassistant"}
    )
    flow = await provider.async_login_flow({})
    result = await flow.async_step_init()
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result = await flow.async_step_init(
        {"username": "incorrect-user", "password": "test-pass"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"

    result = await flow.async_step_init(
        {"username": "TEST-user ", "password": "incorrect-pass"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"

    result = await flow.async_step_init(
        {"username": "test-USER", "password": "test-pass"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["username"] == "test-USER"