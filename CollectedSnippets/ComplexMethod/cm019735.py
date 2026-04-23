async def test_climate_myzone_zone(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_get: AsyncMock,
    mock_update: AsyncMock,
) -> None:
    """Test climate platform myzone zone entity."""

    await add_mock_config(hass)

    # Test Climate Zone Entity
    entity_id = "climate.myzone_zone_open_with_sensor"
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes.get(ATTR_MIN_TEMP) == 16
    assert state.attributes.get(ATTR_MAX_TEMP) == 32
    assert state.attributes.get(ATTR_TEMPERATURE) == 24
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 25

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == "uniqueid-ac1-z01"

    # Test Climate Zone On
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_HVAC_MODE: HVACMode.HEAT_COOL},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()

    # Test Climate Zone Off
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
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: [entity_id], ATTR_TEMPERATURE: 25},
        blocking=True,
    )
    mock_update.assert_called_once()
    mock_update.reset_mock()