async def test_sensors_disappearing(
    hass: HomeAssistant,
    open_api: OpenAPI,
    aioambient: AsyncMock,
    config_entry: ConfigEntry,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that we log errors properly."""

    # Normal state, sensor is available.
    await setup_platform(True, hass, config_entry)
    sensor = hass.states.get("sensor.station_a_relative_pressure")
    assert sensor is not None
    assert float(sensor.state) == pytest.approx(1001.89694313129)

    # Sensor becomes unavailable if the network is unavailable. Log message
    # should only show up once.
    for _ in range(5):
        with patch.object(open_api, "get_device_details", side_effect=RequestError()):
            freezer.tick(timedelta(minutes=10))
            async_fire_time_changed(hass)
            await hass.async_block_till_done()

        sensor = hass.states.get("sensor.station_a_relative_pressure")
        assert sensor is not None
        assert sensor.state == "unavailable"
        assert caplog.text.count("Cannot connect to Ambient Network") == 3

    # Network comes back. Sensor should start reporting again. Log message
    # should only show up once.
    for _ in range(5):
        freezer.tick(timedelta(minutes=10))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        sensor = hass.states.get("sensor.station_a_relative_pressure")
        assert sensor is not None
        assert float(sensor.state) == pytest.approx(1001.89694313129)
        assert caplog.text.count("Fetching ambient_network data recovered") == 1