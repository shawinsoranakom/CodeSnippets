async def _test_sensors(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_devices,
    config,
    entry_unique_id,
) -> None:
    """Test creating AsusWRT default sensors and tracker."""
    config_entry, sensor_prefix = _setup_entry(
        hass, config, SENSORS_DEFAULT, entry_unique_id
    )

    # Create the first device tracker to test mac conversion
    entity_reg = er.async_get(hass)
    for mac, name in {
        MOCK_MACS[0]: "test",
        dr.format_mac(MOCK_MACS[1]): "testtwo",
        MOCK_MACS[1]: "testremove",
    }.items():
        entity_reg.async_get_or_create(
            device_tracker.DOMAIN,
            DOMAIN,
            mac,
            suggested_object_id=name,
            config_entry=config_entry,
            disabled_by=None,
        )

    # initial devices setup
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(f"{device_tracker.DOMAIN}.test").state == STATE_HOME
    assert hass.states.get(f"{device_tracker.DOMAIN}.testtwo").state == STATE_HOME
    assert hass.states.get(f"{sensor_prefix}_sensor_rx_rates").state == "160.0"
    assert hass.states.get(f"{sensor_prefix}_sensor_rx_bytes").state == "60.0"
    assert hass.states.get(f"{sensor_prefix}_sensor_tx_rates").state == "80.0"
    assert hass.states.get(f"{sensor_prefix}_sensor_tx_bytes").state == "50.0"
    assert hass.states.get(f"{sensor_prefix}_devices_connected").state == "2"
    assert hass.states.get(f"{sensor_prefix}_sensor_load_avg1").state == "1.1"
    assert hass.states.get(f"{sensor_prefix}_sensor_load_avg5").state == "1.2"
    assert hass.states.get(f"{sensor_prefix}_sensor_load_avg15").state == "1.3"

    # remove first tracked device
    mock_devices.pop(MOCK_MACS[0])

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # consider home option set, all devices still home but only 1 device connected
    assert hass.states.get(f"{device_tracker.DOMAIN}.test").state == STATE_HOME
    assert hass.states.get(f"{device_tracker.DOMAIN}.testtwo").state == STATE_HOME
    assert hass.states.get(f"{sensor_prefix}_devices_connected").state == "1"

    # add 2 new devices, one unnamed that should be ignored but counted
    mock_devices[MOCK_MACS[2]] = new_device(
        config[CONF_PROTOCOL], MOCK_MACS[2], "192.168.1.4", "TestThree"
    )
    mock_devices[MOCK_MACS[3]] = new_device(
        config[CONF_PROTOCOL], MOCK_MACS[3], "192.168.1.5", None
    )

    # change consider home settings to have status not home of removed tracked device
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_CONSIDER_HOME: 0}
    )
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # consider home option set to 0, device "test" not home
    assert hass.states.get(f"{device_tracker.DOMAIN}.test").state == STATE_NOT_HOME
    assert hass.states.get(f"{device_tracker.DOMAIN}.testtwo").state == STATE_HOME
    assert hass.states.get(f"{device_tracker.DOMAIN}.testthree").state == STATE_HOME
    assert hass.states.get(f"{sensor_prefix}_devices_connected").state == "3"