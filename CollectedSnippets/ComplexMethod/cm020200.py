async def test_reconfigure_validates_and_updates_config(
    hass: HomeAssistant, config_entry: MockConfigEntry, controller: MockHeos
) -> None:
    """Test reconfigure validates host and successfully updates."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    assert config_entry.data[CONF_HOST] == "127.0.0.1"

    # Test reconfigure initially shows form with current host value.
    schema = result["data_schema"]
    assert schema is not None
    host = next(key.default() for key in schema.schema if key == CONF_HOST)
    assert host == "127.0.0.1"
    assert result["errors"] == {}
    assert result["step_id"] == "reconfigure"
    assert result["type"] is FlowResultType.FORM

    # Test reconfigure successfully updates.
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