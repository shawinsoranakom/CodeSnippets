async def test_reauth_flow_missing_one_param_recovers(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    controller: MockHeos,
    user_input: dict[str, str],
    expected_errors: dict[str, str],
) -> None:
    """Test reauth flow signs-in after recovering from only username or password being entered."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    controller.mock_set_connection_state(ConnectionState.CONNECTED)

    # Start the options flow. Entry has not current options.
    result = await config_entry.start_reauth_flow(hass)
    assert config_entry.state is ConfigEntryState.LOADED
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {}
    assert result["type"] is FlowResultType.FORM

    # Enter only username or password
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == expected_errors
    assert result["type"] is FlowResultType.FORM

    # Enter valid credentials
    user_input = {CONF_USERNAME: "user", CONF_PASSWORD: "pass"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    assert controller.sign_in.call_count == 1
    assert controller.sign_out.call_count == 0
    assert config_entry.options[CONF_USERNAME] == user_input[CONF_USERNAME]
    assert config_entry.options[CONF_PASSWORD] == user_input[CONF_PASSWORD]
    assert result["reason"] == "reauth_successful"
    assert result["type"] is FlowResultType.ABORT