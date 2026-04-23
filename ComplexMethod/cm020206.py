async def test_reauth_signs_out(
    hass: HomeAssistant, config_entry: MockConfigEntry, controller: MockHeos
) -> None:
    """Test reauth flow signs-out when credentials cleared and aborts."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    controller.mock_set_connection_state(ConnectionState.CONNECTED)
    result = await config_entry.start_reauth_flow(hass)
    assert config_entry.state is ConfigEntryState.LOADED

    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {}
    assert result["type"] is FlowResultType.FORM

    # Fail to sign-out, show error
    user_input: dict[str, Any] = {}
    controller.sign_out.side_effect = HeosError()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    assert controller.sign_in.call_count == 0
    assert controller.sign_out.call_count == 1
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "unknown"}
    assert result["type"] is FlowResultType.FORM

    # Cleared credentials signs-out, updates options, and aborts
    controller.sign_out.reset_mock()
    controller.sign_out.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    assert controller.sign_in.call_count == 0
    assert controller.sign_out.call_count == 1
    assert CONF_USERNAME not in config_entry.options
    assert CONF_PASSWORD not in config_entry.options
    assert result["reason"] == "reauth_successful"
    assert result["type"] is FlowResultType.ABORT