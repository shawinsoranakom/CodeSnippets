async def test_climate_set_preset_mode(
    hass: HomeAssistant, mock_block_device: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test climate set preset mode service."""
    monkeypatch.delattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "targetTemp")
    monkeypatch.delattr(mock_block_device.blocks[GAS_VALVE_BLOCK_ID], "targetTemp")
    monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "valveError", 0)
    monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "mode", None)
    await init_integration(hass, 1, sleep_period=1000, model=MODEL_VALVE)

    # Make device online
    mock_block_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (state := hass.states.get(ENTITY_ID))
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_NONE

    # Test set Profile2
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "Profile2"},
        blocking=True,
    )

    mock_block_device.set_thermostat_state.assert_called_once_with(
        0, schedule=1, schedule_profile=2
    )

    monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "mode", 2)
    mock_block_device.mock_update()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.attributes[ATTR_PRESET_MODE] == "Profile2"

    # Set preset to none
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: PRESET_NONE},
        blocking=True,
    )

    assert len(mock_block_device.set_thermostat_state.mock_calls) == 2
    mock_block_device.set_thermostat_state.assert_called_with(0, schedule=0)

    monkeypatch.setattr(mock_block_device.blocks[DEVICE_BLOCK_ID], "mode", 0)
    mock_block_device.mock_update()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_NONE