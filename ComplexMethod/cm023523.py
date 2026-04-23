async def test_relay_switch_2pm_sensor(hass: HomeAssistant) -> None:
    """Test setting up creates the relay switch 2PM sensor."""
    await async_setup_component(hass, DOMAIN, {})
    inject_bluetooth_service_info(hass, RELAY_SWITCH_2PM_SERVICE_INFO)

    with patch(
        "homeassistant.components.switchbot.switch.switchbot.SwitchbotRelaySwitch2PM.get_basic_info",
        new=AsyncMock(
            return_value={
                1: {
                    "power": 4.9,
                    "current": 0.1,
                    "voltage": 25,
                    "energy": 0.2,
                },
                2: {
                    "power": 7.9,
                    "current": 0.6,
                    "voltage": 25,
                    "energy": 2.5,
                },
            }
        ),
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
                CONF_NAME: "test-name",
                CONF_SENSOR_TYPE: "relay_switch_2pm",
                CONF_KEY_ID: "ff",
                CONF_ENCRYPTION_KEY: "ffffffffffffffffffffffffffffffff",
            },
            unique_id="aabbccddeeaa",
        )
        entry.add_to_hass(hass)

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 9

    power_sensor_1 = hass.states.get("sensor.test_name_channel_1_power")
    power_sensor_attrs = power_sensor_1.attributes
    assert power_sensor_1.state == "4.9"
    assert power_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Channel 1 Power"
    assert power_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "W"
    assert power_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    voltage_sensor_1 = hass.states.get("sensor.test_name_channel_1_voltage")
    voltage_sensor_1_attrs = voltage_sensor_1.attributes
    assert voltage_sensor_1.state == "25"
    assert voltage_sensor_1_attrs[ATTR_FRIENDLY_NAME] == "test-name Channel 1 Voltage"
    assert voltage_sensor_1_attrs[ATTR_UNIT_OF_MEASUREMENT] == "V"
    assert voltage_sensor_1_attrs[ATTR_STATE_CLASS] == "measurement"

    current_sensor_1 = hass.states.get("sensor.test_name_channel_1_current")
    current_sensor_1_attrs = current_sensor_1.attributes
    assert current_sensor_1.state == "0.1"
    assert current_sensor_1_attrs[ATTR_FRIENDLY_NAME] == "test-name Channel 1 Current"
    assert current_sensor_1_attrs[ATTR_UNIT_OF_MEASUREMENT] == "A"
    assert current_sensor_1_attrs[ATTR_STATE_CLASS] == "measurement"

    energy_sensor_1 = hass.states.get("sensor.test_name_channel_1_energy")
    energy_sensor_1_attrs = energy_sensor_1.attributes
    assert energy_sensor_1.state == "0.2"
    assert energy_sensor_1_attrs[ATTR_FRIENDLY_NAME] == "test-name Channel 1 Energy"
    assert energy_sensor_1_attrs[ATTR_UNIT_OF_MEASUREMENT] == "kWh"
    assert energy_sensor_1_attrs[ATTR_STATE_CLASS] == "total_increasing"

    power_sensor_2 = hass.states.get("sensor.test_name_channel_2_power")
    power_sensor_2_attrs = power_sensor_2.attributes
    assert power_sensor_2.state == "7.9"
    assert power_sensor_2_attrs[ATTR_FRIENDLY_NAME] == "test-name Channel 2 Power"
    assert power_sensor_2_attrs[ATTR_UNIT_OF_MEASUREMENT] == "W"
    assert power_sensor_2_attrs[ATTR_STATE_CLASS] == "measurement"

    voltage_sensor_2 = hass.states.get("sensor.test_name_channel_2_voltage")
    voltage_sensor_2_attrs = voltage_sensor_2.attributes
    assert voltage_sensor_2.state == "25"
    assert voltage_sensor_2_attrs[ATTR_FRIENDLY_NAME] == "test-name Channel 2 Voltage"
    assert voltage_sensor_2_attrs[ATTR_UNIT_OF_MEASUREMENT] == "V"
    assert voltage_sensor_2_attrs[ATTR_STATE_CLASS] == "measurement"

    current_sensor_2 = hass.states.get("sensor.test_name_channel_2_current")
    current_sensor_2_attrs = current_sensor_2.attributes
    assert current_sensor_2.state == "0.6"
    assert current_sensor_2_attrs[ATTR_FRIENDLY_NAME] == "test-name Channel 2 Current"
    assert current_sensor_2_attrs[ATTR_UNIT_OF_MEASUREMENT] == "A"
    assert current_sensor_2_attrs[ATTR_STATE_CLASS] == "measurement"

    energy_sensor_2 = hass.states.get("sensor.test_name_channel_2_energy")
    energy_sensor_2_attrs = energy_sensor_2.attributes
    assert energy_sensor_2.state == "2.5"
    assert energy_sensor_2_attrs[ATTR_FRIENDLY_NAME] == "test-name Channel 2 Energy"
    assert energy_sensor_2_attrs[ATTR_UNIT_OF_MEASUREMENT] == "kWh"
    assert energy_sensor_2_attrs[ATTR_STATE_CLASS] == "total_increasing"

    rssi_sensor = hass.states.get("sensor.test_name_bluetooth_signal")
    rssi_sensor_attrs = rssi_sensor.attributes
    assert rssi_sensor.state == "-60"
    assert rssi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Bluetooth signal"
    assert rssi_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "dBm"
    assert rssi_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()