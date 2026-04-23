async def test_reauth_updates_when_not_connected(
    hass: HomeAssistant, config_entry: MockConfigEntry, controller: MockHeos
) -> None:
    """Test reauth flow signs-in with entered credentials and aborts."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    controller.mock_set_connection_state(ConnectionState.RECONNECTING)

    result = await config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {}
    assert result["type"] is FlowResultType.FORM

    # Valid credentials signs-in, updates options, and aborts
    user_input = {CONF_USERNAME: "user", CONF_PASSWORD: "pass"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    assert controller.sign_in.call_count == 0
    assert controller.sign_out.call_count == 0
    assert config_entry.options[CONF_USERNAME] == user_input[CONF_USERNAME]
    assert config_entry.options[CONF_PASSWORD] == user_input[CONF_PASSWORD]
    assert result["reason"] == "reauth_successful"
    assert result["type"] is FlowResultType.ABORT