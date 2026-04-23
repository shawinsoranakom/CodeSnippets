async def test_legacy_login_flow_validates(
    legacy_data: hass_auth.Data, hass: HomeAssistant
) -> None:
    """Test in legacy mode login flow."""
    legacy_data.add_auth("test-user", "test-pass")
    await legacy_data.async_save()

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
        {"username": "test-user", "password": "incorrect-pass"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"

    result = await flow.async_step_init(
        {"username": "test-user", "password": "test-pass"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["username"] == "test-user"