async def test_relay_switch_1pm_sensor(hass: HomeAssistant) -> None:
    """Test setting up creates the relay switch 1PM sensor."""
    await async_setup_component(hass, DOMAIN, {})
    inject_bluetooth_service_info(hass, WORELAY_SWITCH_1PM_SERVICE_INFO)

    with patch(
        "homeassistant.components.switchbot.switch.switchbot.SwitchbotRelaySwitch.get_basic_info",
        new=AsyncMock(
            return_value={
                "power": 4.9,
                "current": 0.02,
                "voltage": 25,
                "energy": 0.2,
            }
        ),
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
                CONF_NAME: "test-name",
                CONF_SENSOR_TYPE: "relay_switch_1pm",
                CONF_KEY_ID: "ff",
                CONF_ENCRYPTION_KEY: "ffffffffffffffffffffffffffffffff",
            },
            unique_id="aabbccddeeaa",
        )
        entry.add_to_hass(hass)

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 5

    power_sensor = hass.states.get("sensor.test_name_power")
    power_sensor_attrs = power_sensor.attributes
    assert power_sensor.state == "4.9"
    assert power_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Power"
    assert power_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "W"
    assert power_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    voltage_sensor = hass.states.get("sensor.test_name_voltage")
    voltage_sensor_attrs = voltage_sensor.attributes
    assert voltage_sensor.state == "25"
    assert voltage_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Voltage"
    assert voltage_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "V"
    assert voltage_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    current_sensor = hass.states.get("sensor.test_name_current")
    current_sensor_attrs = current_sensor.attributes
    assert current_sensor.state == "0.02"
    assert current_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Current"
    assert current_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "A"
    assert current_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    energy_sensor = hass.states.get("sensor.test_name_energy")
    energy_sensor_attrs = energy_sensor.attributes
    assert energy_sensor.state == "0.2"
    assert energy_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Energy"
    assert energy_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "kWh"
    assert energy_sensor_attrs[ATTR_STATE_CLASS] == "total_increasing"

    rssi_sensor = hass.states.get("sensor.test_name_bluetooth_signal")
    rssi_sensor_attrs = rssi_sensor.attributes
    assert rssi_sensor.state == "-60"
    assert rssi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Bluetooth signal"
    assert rssi_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "dBm"
    assert rssi_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()