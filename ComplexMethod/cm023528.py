async def test_air_purifier_sensor(hass: HomeAssistant) -> None:
    """Test setting up creates the air purifier sensor."""
    await async_setup_component(hass, DOMAIN, {})
    inject_bluetooth_service_info(hass, AIR_PURIFIER_TABLE_US_SERVICE_INFO)

    with patch(
        "homeassistant.components.switchbot.switch.switchbot.SwitchbotAirPurifier.get_basic_info",
        new=AsyncMock(
            return_value={
                "pm25": 1,
                "aqi_level": "excellent",
            }
        ),
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
                CONF_NAME: "test-name",
                CONF_SENSOR_TYPE: "air_purifier_table_us",
                CONF_KEY_ID: "ff",
                CONF_ENCRYPTION_KEY: "ffffffffffffffffffffffffffffffff",
            },
            unique_id="aabbccddeeaa",
        )
        entry.add_to_hass(hass)

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert {state.entity_id for state in hass.states.async_all("sensor")} == {
        "sensor.test_name_pm2_5",
        "sensor.test_name_air_quality_level",
        "sensor.test_name_bluetooth_signal",
    }

    pm25_sensor = hass.states.get("sensor.test_name_pm2_5")
    pm25_sensor_attrs = pm25_sensor.attributes
    assert pm25_sensor.state == "1"
    assert pm25_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name PM2.5"
    assert pm25_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "μg/m³"
    assert pm25_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    aqi_sensor = hass.states.get("sensor.test_name_air_quality_level")
    aqi_sensor_attrs = aqi_sensor.attributes
    assert aqi_sensor.state == "excellent"
    assert aqi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Air quality level"

    rssi_sensor = hass.states.get("sensor.test_name_bluetooth_signal")
    rssi_sensor_attrs = rssi_sensor.attributes
    assert rssi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Bluetooth signal"
    assert rssi_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "dBm"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()