async def test_no_sensor_and_water_state(
    hass: HomeAssistant,
    controller: Controller,
    controller_water_use_summary: ControllerWaterUseSummary,
    mock_add_config_entry: Callable[[], Awaitable[MockConfigEntry]],
) -> None:
    """Test rain sensor, flow sensor, and water use in the absence of flow and rain sensors."""
    controller.sensors = []
    controller_water_use_summary.total_use = None
    controller_water_use_summary.total_active_use = None
    controller_water_use_summary.total_inactive_use = None
    controller_water_use_summary.active_use_by_zone_id = {}
    await mock_add_config_entry()

    assert hass.states.get("sensor.zone_one_daily_active_water_use") is None
    assert hass.states.get("sensor.zone_two_daily_active_water_use") is None
    assert hass.states.get("sensor.home_controller_daily_active_water_use") is None
    assert hass.states.get("sensor.home_controller_daily_inactive_water_use") is None
    assert hass.states.get("binary_sensor.home_controller_rain_sensor") is None

    sensor = hass.states.get("sensor.home_controller_daily_active_watering_time")
    assert sensor is not None
    assert sensor.state == "123.0"

    sensor = hass.states.get("sensor.zone_one_daily_active_watering_time")
    assert sensor is not None
    assert sensor.state == "123.0"

    sensor = hass.states.get("sensor.zone_two_daily_active_watering_time")
    assert sensor is not None
    assert sensor.state == "0.0"

    sensor = hass.states.get("binary_sensor.home_controller_connectivity")
    assert sensor is not None
    assert sensor.state == "on"