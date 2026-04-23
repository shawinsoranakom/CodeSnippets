async def test_climate_hvac_mode(
    hass: HomeAssistant,
    mock_block_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    entity_registry: EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test climate hvac mode service."""
    monkeypatch.delattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "targetTemp")
    monkeypatch.setattr(
        mock_block_device.blocks[SENSOR_BLOCK_ID],
        "sensor_ids",
        {"battery": 98, "valvePos": 50, "targetTemp": 21.0},
    )
    monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0)
    monkeypatch.delattr(mock_block_device.blocks[EMETER_BLOCK_ID], "targetTemp")
    monkeypatch.delattr(mock_block_device.blocks[GAS_VALVE_BLOCK_ID], "targetTemp")
    await init_integration(hass, 1, sleep_period=1000, model=MODEL_VALVE)

    # Make device online
    mock_block_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    # Test initial hvac mode - off
    assert hass.states.get(ENTITY_ID) == snapshot(name=f"{ENTITY_ID}-state")

    assert entity_registry.async_get(ENTITY_ID) == snapshot(name=f"{ENTITY_ID}-entry")

    # Test set hvac mode heat
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )
    mock_block_device.set_thermostat_state.assert_called_once_with(
        0, target_t_enabled=1, target_t=20.0
    )

    monkeypatch.setattr(mock_block_device.blocks[SENSOR_BLOCK_ID], "targetTemp", 20.0)
    mock_block_device.mock_update()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == HVACMode.HEAT

    # Test set hvac mode off
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )

    mock_block_device.set_thermostat_state.assert_called_with(
        0, target_t_enabled=1, target_t=4.0
    )

    monkeypatch.setattr(mock_block_device.blocks[SENSOR_BLOCK_ID], "targetTemp", 4.0)
    mock_block_device.mock_update()
    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == HVACMode.OFF

    # Test unavailable on error
    monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 1)
    mock_block_device.mock_update()
    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == STATE_UNAVAILABLE