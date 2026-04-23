async def test_availability(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, exc: Exception
) -> None:
    """Ensure that we mark the entities unavailable correctly when device causes an error."""
    nam_data = await async_load_json_object_fixture(hass, "nam_data.json", DOMAIN)

    await init_integration(hass)

    state = hass.states.get("sensor.nettigo_air_monitor_bme280_temperature")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "7.56"

    with (
        patch("homeassistant.components.nam.NettigoAirMonitor.initialize"),
        patch(
            "homeassistant.components.nam.NettigoAirMonitor._async_http_request",
            side_effect=exc,
        ),
    ):
        freezer.tick(DEFAULT_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.nettigo_air_monitor_bme280_temperature")
    assert state
    assert state.state == STATE_UNAVAILABLE

    update_response = Mock(json=AsyncMock(return_value=nam_data))
    with (
        patch("homeassistant.components.nam.NettigoAirMonitor.initialize"),
        patch(
            "homeassistant.components.nam.NettigoAirMonitor._async_http_request",
            return_value=update_response,
        ),
    ):
        freezer.tick(DEFAULT_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.nettigo_air_monitor_bme280_temperature")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "7.56"