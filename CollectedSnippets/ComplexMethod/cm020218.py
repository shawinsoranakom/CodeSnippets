async def test_cpu_sensors_http_fail(
    hass: HomeAssistant, connect_http_sens_fail
) -> None:
    """Test fail creating AsusWRT cpu sensors."""
    _ = connect_http_sens_fail([AsusData.CPU])
    config_entry, sensor_prefix = _setup_entry(hass, CONFIG_DATA_HTTP, SENSORS_CPU)
    config_entry.add_to_hass(hass)

    # initial devices setup
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # assert cpu availability exception is handled correctly
    assert not hass.states.get(f"{sensor_prefix}_cpu1_usage")
    assert not hass.states.get(f"{sensor_prefix}_cpu2_usage")
    assert not hass.states.get(f"{sensor_prefix}_cpu3_usage")
    assert not hass.states.get(f"{sensor_prefix}_cpu4_usage")
    assert not hass.states.get(f"{sensor_prefix}_cpu5_usage")
    assert not hass.states.get(f"{sensor_prefix}_cpu6_usage")
    assert not hass.states.get(f"{sensor_prefix}_cpu7_usage")
    assert not hass.states.get(f"{sensor_prefix}_cpu8_usage")
    assert not hass.states.get(f"{sensor_prefix}_cpu_total_usage")