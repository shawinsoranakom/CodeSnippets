async def test_reauth_clears_when_not_connected(
    hass: HomeAssistant, config_entry: MockConfigEntry, controller: MockHeos
) -> None:
    """Test reauth flow signs-out with entered credentials and aborts."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    controller.mock_set_connection_state(ConnectionState.RECONNECTING)

    result = await config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {}
    assert result["type"] is FlowResultType.FORM

    # Valid credentials signs-out, updates options, and aborts
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert controller.sign_in.call_count == 0
    assert controller.sign_out.call_count == 0
    assert config_entry.options == {}
    assert result["reason"] == "reauth_successful"
    assert result["type"] is FlowResultType.ABORT