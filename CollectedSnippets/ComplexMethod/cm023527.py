async def test_keypad_vision_sensor(
    hass: HomeAssistant,
    adv_info: BluetoothServiceInfoBleak,
    sensor_type: str,
    charging_state: str,
) -> None:
    """Test setting up creates the sensors for Keypad Vision (Pro)."""
    await async_setup_component(hass, DOMAIN, {})
    inject_bluetooth_service_info(hass, adv_info)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_NAME: "test-name",
            CONF_SENSOR_TYPE: sensor_type,
            CONF_KEY_ID: "ff",
            CONF_ENCRYPTION_KEY: "ffffffffffffffffffffffffffffffff",
        },
        unique_id="aabbccddeeff",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.switchbot.sensor.switchbot.SwitchbotKeypadVision.update",
        return_value=True,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert len(hass.states.async_all("sensor")) == 2
        assert len(hass.states.async_all("binary_sensor")) == 2

        battery_sensor = hass.states.get("sensor.test_name_battery")
        battery_sensor_attrs = battery_sensor.attributes
        assert battery_sensor
        assert battery_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Battery"
        assert battery_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

        rssi_sensor = hass.states.get("sensor.test_name_bluetooth_signal")
        rssi_sensor_attrs = rssi_sensor.attributes
        assert rssi_sensor
        assert rssi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Bluetooth signal"
        assert rssi_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "dBm"

        tamper_sensor = hass.states.get("binary_sensor.test_name_tamper")
        tamper_sensor_attrs = tamper_sensor.attributes
        assert tamper_sensor
        assert tamper_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Tamper"
        assert tamper_sensor.state == STATE_OFF

        charging_sensor = hass.states.get("binary_sensor.test_name_charging")
        charging_sensor_attrs = charging_sensor.attributes
        assert charging_sensor
        assert charging_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Charging"
        assert charging_sensor.state == charging_state

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()