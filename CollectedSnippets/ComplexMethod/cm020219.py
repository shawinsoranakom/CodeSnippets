async def test_cpu_sensors_http(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    connect_http,
    connect_http_sens_detect,
) -> None:
    """Test creating AsusWRT cpu sensors."""
    config_entry, sensor_prefix = _setup_entry(hass, CONFIG_DATA_HTTP, SENSORS_CPU)
    config_entry.add_to_hass(hass)

    # initial devices setup
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # assert cpu sensors available
    assert hass.states.get(f"{sensor_prefix}_cpu1_usage").state == "0.1"
    assert hass.states.get(f"{sensor_prefix}_cpu2_usage").state == "0.2"
    assert hass.states.get(f"{sensor_prefix}_cpu3_usage").state == "0.3"
    assert hass.states.get(f"{sensor_prefix}_cpu4_usage").state == "0.4"
    assert hass.states.get(f"{sensor_prefix}_cpu5_usage").state == "0.5"
    assert hass.states.get(f"{sensor_prefix}_cpu6_usage").state == "0.6"
    assert hass.states.get(f"{sensor_prefix}_cpu7_usage").state == "0.7"
    assert hass.states.get(f"{sensor_prefix}_cpu8_usage").state == "0.8"
    assert hass.states.get(f"{sensor_prefix}_cpu_total_usage").state == "0.9"