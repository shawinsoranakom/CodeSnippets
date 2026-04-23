async def test_presence_sensor_without_battery(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors for Presence Sensor without battery."""
    await async_setup_component(hass, DOMAIN, {})
    inject_bluetooth_service_info(hass, PRESENCE_SENSOR_SERVICE_INFO)

    with patch(
        "homeassistant.components.switchbot.sensor.switchbot.parse_advertisement_data",
        return_value=SwitchBotAdvertisement(
            address="AA:BB:CC:DD:EE:FF",
            data={
                "rawAdvData": b"\x00 d\x00\x10\xcc\xc8",
                "data": {
                    "sequence_number": 190,
                    "adaptive_state": True,
                    "motion_detected": True,
                    "battery_range": ">=60%",
                    "trigger_flag": 0,
                    "led_state": True,
                    "lightLevel": 2,
                },
                "model": b"\x00\x10\xcc\xc8",
                "isEncrypted": False,
                "modelFriendlyName": "Presence Sensor",
                "modelName": SwitchbotModel.PRESENCE_SENSOR,
            },
            device=PRESENCE_SENSOR_SERVICE_INFO.device,
            rssi=PRESENCE_SENSOR_SERVICE_INFO.rssi,
            active=True,
        ),
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
                CONF_NAME: "test-name",
                CONF_SENSOR_TYPE: "presence_sensor",
            },
            unique_id="aabbccddeeff",
        )
        entry.add_to_hass(hass)

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert len(hass.states.async_all("sensor")) == 3
        assert len(hass.states.async_all("binary_sensor")) == 1

        battery_range_sensor = hass.states.get("sensor.test_name_battery_range")
        assert battery_range_sensor is not None
        br_sensor_attrs = battery_range_sensor.attributes
        assert battery_range_sensor.state == "high"
        assert br_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Battery range"

        light_level_sensor = hass.states.get("sensor.test_name_light_level")
        light_level_sensor_attrs = light_level_sensor.attributes
        assert light_level_sensor
        assert light_level_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Light level"

        rssi_sensor = hass.states.get("sensor.test_name_bluetooth_signal")
        rssi_sensor_attrs = rssi_sensor.attributes
        assert rssi_sensor
        assert rssi_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Bluetooth signal"
        assert rssi_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "dBm"

        occupancy_sensor = hass.states.get("binary_sensor.test_name_occupancy")
        occupancy_sensor_attrs = occupancy_sensor.attributes
        assert occupancy_sensor
        assert occupancy_sensor_attrs[ATTR_FRIENDLY_NAME] == "test-name Occupancy"

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()