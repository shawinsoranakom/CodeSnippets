async def test_exception_handling_battery_sensor(
    hass: HomeAssistant,
    mock_psutil: Mock,
    mock_os: Mock,
    freezer: FrozenDateTimeFactory,
    mock_config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
    exception_class: type[Exception],
) -> None:
    """Test the battery failures."""
    mock_psutil.sensors_battery.side_effect = exception_class(
        "[Errno 2] No such file or directory: '/sys/class/power_supply'"
    )
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert (temp_entity := hass.states.get("sensor.system_monitor_battery"))
    assert temp_entity.state == STATE_UNAVAILABLE
    assert (temp_entity := hass.states.get("sensor.system_monitor_battery_empty"))
    assert temp_entity.state == STATE_UNAVAILABLE

    assert "OS error when accessing battery sensors" in caplog.text

    mock_psutil.sensors_battery.side_effect = None
    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (temp_entity := hass.states.get("sensor.system_monitor_battery"))
    assert temp_entity.state == "93"
    assert (temp_entity := hass.states.get("sensor.system_monitor_battery_empty"))
    assert temp_entity.state == "2024-02-24T19:38:00+00:00"