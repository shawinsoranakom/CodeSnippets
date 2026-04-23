async def test_options_flow_signs_out(
    hass: HomeAssistant, config_entry: MockConfigEntry, controller: MockHeos
) -> None:
    """Test options flow signs-out when credentials cleared."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    controller.mock_set_connection_state(ConnectionState.CONNECTED)

    # Start the options flow. Entry has not current options.
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["step_id"] == "init"
    assert result["errors"] == {}
    assert result["type"] is FlowResultType.FORM

    # Fail to sign-out, show error
    user_input: dict[str, Any] = {}
    controller.sign_out.side_effect = HeosError()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )
    assert controller.sign_in.call_count == 0
    assert controller.sign_out.call_count == 1
    assert result["step_id"] == "init"
    assert result["errors"] == {"base": "unknown"}
    assert result["type"] is FlowResultType.FORM

    # Clear credentials
    controller.sign_out.reset_mock()
    controller.sign_out.side_effect = None
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )
    assert controller.sign_in.call_count == 0
    assert controller.sign_out.call_count == 1
    assert result["data"] == user_input
    assert result["type"] is FlowResultType.CREATE_ENTRY