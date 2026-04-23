async def test_availability(ismartgateapi_mock, hass: HomeAssistant) -> None:
    """Test availability."""
    bat_attributes = {
        "device_class": "battery",
        "door_id": 1,
        "friendly_name": "mycontroller Door1 battery",
        "sensor_id": "ABCD",
        "state_class": "measurement",
        "unit_of_measurement": "%",
    }
    temp_attributes = {
        "device_class": "temperature",
        "door_id": 1,
        "friendly_name": "mycontroller Door1 temperature",
        "sensor_id": "ABCD",
        "unit_of_measurement": "°C",
        "state_class": "measurement",
    }

    sensor_response = _mocked_ismartgate_sensor_response(35, -4.0)
    api = MagicMock(ISmartGateApi)
    api.async_info.return_value = sensor_response
    ismartgateapi_mock.return_value = api

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        title="mycontroller",
        data={
            CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )
    config_entry.add_to_hass(hass)

    assert hass.states.get("cover.mycontroller_door1") is None
    assert hass.states.get("cover.mycontroller_door2") is None
    assert hass.states.get("cover.mycontroller_door3") is None
    assert hass.states.get("sensor.mycontroller_door1_battery") is None
    assert hass.states.get("sensor.mycontroller_door2_battery") is None
    assert hass.states.get("sensor.mycontroller_door3_battery") is None
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1")
    assert hass.states.get("cover.mycontroller_door2")
    assert hass.states.get("cover.mycontroller_door3")
    assert hass.states.get("sensor.mycontroller_door1_battery").state == "35"
    assert hass.states.get("sensor.mycontroller_door2_battery") is None
    assert hass.states.get("sensor.mycontroller_door3_battery") is None
    assert hass.states.get("sensor.mycontroller_door1_temperature").state == "-4.0"
    assert hass.states.get("sensor.mycontroller_door2_temperature") is None
    assert hass.states.get("sensor.mycontroller_door3_temperature") is None
    assert (
        hass.states.get("sensor.mycontroller_door1_battery").attributes[
            ATTR_DEVICE_CLASS
        ]
        == SensorDeviceClass.BATTERY
    )
    assert (
        hass.states.get("sensor.mycontroller_door1_temperature").attributes[
            ATTR_DEVICE_CLASS
        ]
        == SensorDeviceClass.TEMPERATURE
    )
    assert (
        hass.states.get("sensor.mycontroller_door1_temperature").attributes[
            ATTR_UNIT_OF_MEASUREMENT
        ]
        == "°C"
    )

    api.async_info.side_effect = Exception("Error")

    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert (
        hass.states.get("sensor.mycontroller_door1_battery").state == STATE_UNAVAILABLE
    )
    assert (
        hass.states.get("sensor.mycontroller_door1_temperature").state
        == STATE_UNAVAILABLE
    )

    api.async_info.side_effect = None
    api.async_info.return_value = sensor_response
    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.mycontroller_door1_battery").state == "35"
    assert (
        dict(hass.states.get("sensor.mycontroller_door1_battery").attributes)
        == bat_attributes
    )
    assert (
        dict(hass.states.get("sensor.mycontroller_door1_temperature").attributes)
        == temp_attributes
    )