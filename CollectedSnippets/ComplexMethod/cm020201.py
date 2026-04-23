async def test_reconfigure_cannot_connect_recovers(
    hass: HomeAssistant, config_entry: MockConfigEntry, controller: MockHeos
) -> None:
    """Test reconfigure cannot connect and recovers."""
    controller.connect.side_effect = HeosError()
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    assert config_entry.data[CONF_HOST] == "127.0.0.1"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.2"},
    )

    assert controller.connect.call_count == 1
    assert controller.disconnect.call_count == 1
    schema = result["data_schema"]
    assert schema is not None
    host = next(key.default() for key in schema.schema if key == CONF_HOST)
    assert host == "127.0.0.2"
    errors = result["errors"]
    assert errors is not None
    assert errors[CONF_HOST] == "cannot_connect"
    assert result["step_id"] == "reconfigure"
    assert result["type"] is FlowResultType.FORM

    # Test reconfigure recovers and successfully updates.
    controller.connect.side_effect = None
    controller.connect.reset_mock()
    controller.disconnect.reset_mock()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.2"},
    )
    assert controller.connect.call_count == 2  # Also called when entry reloaded
    assert controller.disconnect.call_count == 1
    assert config_entry.data == {CONF_HOST: "127.0.0.2"}
    assert config_entry.unique_id == DOMAIN
    assert result["reason"] == "reconfigure_successful"
    assert result["type"] is FlowResultType.ABORT