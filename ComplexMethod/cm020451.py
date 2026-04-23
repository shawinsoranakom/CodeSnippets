async def test_sensor_update_fail(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    electricity_maps: AsyncMock,
    error: Exception,
) -> None:
    """Test sensor error handling."""
    assert (state := hass.states.get("sensor.electricity_maps_co2_intensity"))
    assert state.state == "45.9862319009581"
    assert len(electricity_maps.mock_calls) == 1

    electricity_maps.carbon_intensity_for_home_assistant.side_effect = error

    freezer.tick(timedelta(minutes=20))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get("sensor.electricity_maps_co2_intensity"))
    assert state.state == "unavailable"
    assert len(electricity_maps.mock_calls) == 2

    # reset mock and test if entity is available again
    electricity_maps.carbon_intensity_for_home_assistant.side_effect = None

    freezer.tick(timedelta(minutes=20))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get("sensor.electricity_maps_co2_intensity"))
    assert state.state == "45.9862319009581"
    assert len(electricity_maps.mock_calls) == 3