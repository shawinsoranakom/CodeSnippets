async def test_options_flow_missing_one_param_recovers(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    controller: MockHeos,
    user_input: dict[str, str],
    expected_errors: dict[str, str],
) -> None:
    """Test options flow signs-in after recovering from only username or password being entered."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    controller.mock_set_connection_state(ConnectionState.CONNECTED)

    # Start the options flow. Entry has not current options.
    assert CONF_USERNAME not in config_entry.options
    assert CONF_PASSWORD not in config_entry.options
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["step_id"] == "init"
    assert result["errors"] == {}
    assert result["type"] is FlowResultType.FORM

    # Enter only username or password
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )
    assert result["step_id"] == "init"
    assert result["errors"] == expected_errors
    assert result["type"] is FlowResultType.FORM

    # Enter valid credentials
    user_input = {CONF_USERNAME: "user", CONF_PASSWORD: "pass"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )
    assert controller.sign_in.call_count == 1
    assert controller.sign_out.call_count == 0
    assert result["data"] == user_input
    assert result["type"] is FlowResultType.CREATE_ENTRY