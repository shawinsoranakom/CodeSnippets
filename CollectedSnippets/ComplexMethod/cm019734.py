async def test_climate_myzone_main(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_get: AsyncMock,
    mock_update: AsyncMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test climate platform main entity."""

    await add_mock_config(hass)

    # Test MyZone main climate entity
    entity_id = "climate.myzone"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == HVACMode.FAN_ONLY
    assert state.attributes.get(ATTR_MIN_TEMP) == 16
    assert state.attributes.get(ATTR_MAX_TEMP) == 32
    assert state.attributes.get(ATTR_TEMPERATURE) == 24
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 25

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1"

    # Test setting HVAC Mode

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_HVAC_MODE: HVACMode.COOL},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_HVAC_MODE: HVACMode.FAN_ONLY},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    # Test Turning Off with HVAC Mode
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_FAN_MODE: FAN_LOW},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    # Test changing Temperature
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_TEMPERATURE: 25},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    # Test Turning On
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    # Test Turning Off
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    # Change Preset
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_PRESET_MODE: ADVANTAGE_AIR_MYAUTO},
        blocking=True,
    )
    mock_update.assert_called_once()
    assert mock_update.call_args[0][0] == snapshot(name=f"{entity_id}-preset")
    mock_update.reset_mock()

    # Test setting HEAT COOL when its not supported
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: [entity_id], ATTR_HVAC_MODE: HVACMode.HEAT_COOL},
            blocking=True,
        )