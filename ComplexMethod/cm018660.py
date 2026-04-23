async def test_options_remove_sensor(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    config_entry,
    setup_config_entry,
) -> None:
    """Test removing a sensor via the options flow."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "remove_sensor"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "remove_sensor"

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, str(TEST_SENSOR_INDEX1))}
    )
    assert device_entry is not None
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"sensor_device_id": device_entry.id},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "sensor_indices": [],
    }

    assert config_entry.options["sensor_indices"] == []
    # Unload to make sure the update does not run after the
    # mock is removed.
    await hass.config_entries.async_unload(config_entry.entry_id)