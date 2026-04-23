async def test_coordinator_update_handler(
    hass: HomeAssistant, discovery, device
) -> None:
    """Test for coordinator update handler."""
    await async_setup_gree(hass)
    await hass.async_block_till_done()

    entity: GreeClimateEntity = hass.data[CLIMATE_DOMAIN].get_entity(ENTITY_ID)
    assert entity is not None

    # Initial state
    assert entity.temperature_unit == UnitOfTemperature.CELSIUS
    assert entity.min_temp == TEMP_MIN
    assert entity.max_temp == TEMP_MAX

    # Set unit to FAHRENHEIT
    device().temperature_units = 1
    entity.coordinator.async_set_updated_data(UnitOfTemperature.FAHRENHEIT)
    await hass.async_block_till_done()

    assert entity.temperature_unit == UnitOfTemperature.FAHRENHEIT
    assert entity.min_temp == TEMP_MIN_F
    assert entity.max_temp == TEMP_MAX_F

    # Set unit back to CELSIUS
    device().temperature_units = 0
    entity.coordinator.async_set_updated_data(UnitOfTemperature.CELSIUS)
    await hass.async_block_till_done()

    assert entity.temperature_unit == UnitOfTemperature.CELSIUS
    assert entity.min_temp == TEMP_MIN
    assert entity.max_temp == TEMP_MAX