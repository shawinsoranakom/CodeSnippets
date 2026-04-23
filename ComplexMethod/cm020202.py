async def test_options_flow_signs_in(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    controller: MockHeos,
    error: HeosError,
    expected_error_key: str,
) -> None:
    """Test options flow signs-in with entered credentials."""
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

    # Invalid credentials, system error, or unexpected error.
    user_input = {CONF_USERNAME: "user", CONF_PASSWORD: "pass"}
    controller.sign_in.side_effect = error
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )
    assert controller.sign_in.call_count == 1
    assert controller.sign_out.call_count == 0
    assert result["step_id"] == "init"
    assert result["errors"] == {"base": expected_error_key}
    assert result["type"] is FlowResultType.FORM

    # Valid credentials signs-in and creates entry
    controller.sign_in.reset_mock()
    controller.sign_in.side_effect = None
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )
    assert controller.sign_in.call_count == 1
    assert controller.sign_out.call_count == 0
    assert result["data"] == user_input
    assert result["type"] is FlowResultType.CREATE_ENTRY