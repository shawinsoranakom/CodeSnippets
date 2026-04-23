async def test_block_restored_climate_us_customary(
    hass: HomeAssistant,
    mock_block_device: Mock,
    device_registry: DeviceRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test block restored climate with US CUSTOMARY unit system."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    monkeypatch.delattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "targetTemp")
    monkeypatch.delattr(mock_block_device.blocks[GAS_VALVE_BLOCK_ID], "targetTemp")
    monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0)
    monkeypatch.delattr(mock_block_device.blocks[EMETER_BLOCK_ID], "targetTemp")
    entry = await init_integration(hass, 1, sleep_period=1000, skip_setup=True)
    device = register_device(device_registry, entry)
    entity_id = register_entity(
        hass,
        CLIMATE_DOMAIN,
        "test_name",
        "sensor_0",
        entry,
        device_id=device.id,
    )
    attrs = {"current_temperature": 67, "temperature": 39}
    extra_data = {"last_target_temp": 10.0}
    mock_restore_cache_with_extra_data(
        hass, ((State(entity_id, HVACMode.OFF, attributes=attrs), extra_data),)
    )

    monkeypatch.setattr(mock_block_device, "initialized", False)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == HVACMode.OFF
    assert state.attributes.get(ATTR_TEMPERATURE) == 39
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 67

    # Partial update, should not change state
    mock_block_device.mock_update()
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == HVACMode.OFF
    assert state.attributes.get(ATTR_TEMPERATURE) == 39
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 67

    # Make device online
    monkeypatch.setattr(mock_block_device, "initialized", True)
    monkeypatch.setattr(mock_block_device.blocks[SENSOR_BLOCK_ID], "targetTemp", 4.0)
    monkeypatch.setattr(mock_block_device.blocks[SENSOR_BLOCK_ID], "temp", 18.2)
    mock_block_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (state := hass.states.get(entity_id))
    assert state.state == HVACMode.OFF
    assert state.attributes.get(ATTR_TEMPERATURE) == 39
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 65

    # Test set hvac mode heat, target temp should be set to last target temp (10.0/50)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )
    mock_block_device.set_thermostat_state.assert_called_once_with(
        0, target_t_enabled=1, target_t=10.0
    )

    monkeypatch.setattr(mock_block_device.blocks[SENSOR_BLOCK_ID], "targetTemp", 10.0)
    mock_block_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == HVACMode.HEAT
    assert state.attributes.get(ATTR_TEMPERATURE) == 50