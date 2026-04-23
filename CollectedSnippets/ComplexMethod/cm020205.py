async def test_reauth_signs_in_aborts(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    controller: MockHeos,
    error: HeosError,
    expected_error_key: str,
) -> None:
    """Test reauth flow signs-in with entered credentials and aborts."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    controller.mock_set_connection_state(ConnectionState.CONNECTED)
    result = await config_entry.start_reauth_flow(hass)
    assert config_entry.state is ConfigEntryState.LOADED

    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {}
    assert result["type"] is FlowResultType.FORM

    # Invalid credentials, system error, or unexpected error.
    user_input = {CONF_USERNAME: "user", CONF_PASSWORD: "pass"}
    controller.sign_in.side_effect = error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    assert controller.sign_in.call_count == 1
    assert controller.sign_out.call_count == 0
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": expected_error_key}
    assert result["type"] is FlowResultType.FORM

    # Valid credentials signs-in, updates options, and aborts
    controller.sign_in.reset_mock()
    controller.sign_in.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    assert controller.sign_in.call_count == 1
    assert controller.sign_out.call_count == 0
    assert config_entry.options[CONF_USERNAME] == user_input[CONF_USERNAME]
    assert config_entry.options[CONF_PASSWORD] == user_input[CONF_PASSWORD]
    assert result["reason"] == "reauth_successful"
    assert result["type"] is FlowResultType.ABORT