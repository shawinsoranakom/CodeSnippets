async def test_leak_sensor(hass: HomeAssistant) -> None:
    """Test setting up the leak detector."""
    await async_setup_component(hass, DOMAIN, {})
    inject_bluetooth_service_info(hass, LEAK_SERVICE_INFO)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
            CONF_NAME: "test-name",
            CONF_SENSOR_TYPE: "leak",
        },
        unique_id="aabbccddeeaa",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    battery_sensor = hass.states.get("sensor.test_name_battery")
    battery_sensor_attrs = battery_sensor.attributes
    assert battery_sensor.state == "86"
    assert battery_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Battery"
    assert battery_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert battery_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    rssi_sensor = hass.states.get("sensor.test_name_bluetooth_signal")
    rssi_sensor_attrs = rssi_sensor.attributes
    assert rssi_sensor.state == "-60"
    assert rssi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Bluetooth signal"
    assert rssi_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "dBm"

    leak_sensor = hass.states.get("binary_sensor.test_name")
    leak_sensor_attrs = leak_sensor.attributes
    assert leak_sensor.state == "off"
    assert leak_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()