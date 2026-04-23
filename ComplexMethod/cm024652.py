async def test_exception_handling_disk_sensor(
    hass: HomeAssistant,
    mock_psutil: Mock,
    mock_added_config_entry: ConfigEntry,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the sensor."""
    disk_sensor = hass.states.get("sensor.system_monitor_disk_free")
    assert disk_sensor is not None
    assert disk_sensor.state == "200.0"  # GiB

    mock_psutil.disk_usage.return_value = None
    mock_psutil.disk_usage.side_effect = OSError("Could not update /")

    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert "OS error for /" in caplog.text

    disk_sensor = hass.states.get("sensor.system_monitor_disk_free")
    assert disk_sensor is not None
    assert disk_sensor.state == STATE_UNAVAILABLE

    mock_psutil.disk_usage.return_value = None
    mock_psutil.disk_usage.side_effect = PermissionError("No access to /")

    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert "OS error for /" in caplog.text

    disk_sensor = hass.states.get("sensor.system_monitor_disk_free")
    assert disk_sensor is not None
    assert disk_sensor.state == STATE_UNAVAILABLE

    mock_psutil.disk_usage.return_value = sdiskusage(
        500 * 1024**3, 350 * 1024**3, 150 * 1024**3, 70.0
    )
    mock_psutil.disk_usage.side_effect = None

    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    disk_sensor = hass.states.get("sensor.system_monitor_disk_free")
    assert disk_sensor is not None
    assert disk_sensor.state == "150.0"
    assert disk_sensor.attributes["unit_of_measurement"] == "GiB"

    disk_sensor = hass.states.get("sensor.system_monitor_disk_usage")
    assert disk_sensor is not None
    assert disk_sensor.state == "70.0"
    assert disk_sensor.attributes["unit_of_measurement"] == "%"