async def test_fan_sensors(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors."""
    await async_setup_component(hass, DOMAIN, {})
    inject_bluetooth_service_info(hass, CIRCULATOR_FAN_SERVICE_INFO)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
            CONF_NAME: "test-name",
            CONF_PASSWORD: "test-password",
            CONF_SENSOR_TYPE: "circulator_fan",
        },
        unique_id="aabbccddeeff",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.switchbot.fan.switchbot.SwitchbotFan.update",
        return_value=True,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert len(hass.states.async_all("sensor")) == 2

        battery_sensor = hass.states.get("sensor.test_name_battery")
        battery_sensor_attrs = battery_sensor.attributes
        assert battery_sensor.state == "82"
        assert battery_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Battery"
        assert battery_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "%"
        assert battery_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

        rssi_sensor = hass.states.get("sensor.test_name_bluetooth_signal")
        rssi_sensor_attrs = rssi_sensor.attributes
        assert rssi_sensor.state == "-60"
        assert rssi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Bluetooth signal"
        assert rssi_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "dBm"

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()