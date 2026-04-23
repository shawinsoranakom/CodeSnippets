async def test_sensor_update(gogogate2api_mock, hass: HomeAssistant) -> None:
    """Test data update."""

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

    api = MagicMock(GogoGate2Api)
    api.async_activate.return_value = GogoGate2ActivateResponse(result=True)
    api.async_info.return_value = _mocked_gogogate_sensor_response(25, 7.0)
    gogogate2api_mock.return_value = api

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        title="mycontroller",
        data={
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
    assert hass.states.get("sensor.mycontroller_door1_temperature") is None
    assert hass.states.get("sensor.mycontroller_door2_temperature") is None
    assert hass.states.get("sensor.mycontroller_door3_temperature") is None
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("cover.mycontroller_door1")
    assert hass.states.get("cover.mycontroller_door2")
    assert hass.states.get("cover.mycontroller_door3")
    assert hass.states.get("sensor.mycontroller_door1_battery").state == "25"
    assert (
        dict(hass.states.get("sensor.mycontroller_door1_battery").attributes)
        == bat_attributes
    )
    assert hass.states.get("sensor.mycontroller_door2_battery") is None
    assert hass.states.get("sensor.mycontroller_door2_battery") is None
    assert hass.states.get("sensor.mycontroller_door1_temperature").state == "7.0"
    assert (
        dict(hass.states.get("sensor.mycontroller_door1_temperature").attributes)
        == temp_attributes
    )
    assert hass.states.get("sensor.mycontroller_door2_temperature") is None
    assert hass.states.get("sensor.mycontroller_door3_temperature") is None

    api.async_info.return_value = _mocked_gogogate_sensor_response(40, 10.0)
    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.mycontroller_door1_battery").state == "40"
    assert hass.states.get("sensor.mycontroller_door1_temperature").state == "10.0"

    api.async_info.return_value = _mocked_gogogate_sensor_response(None, None)
    async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.mycontroller_door1_battery").state == STATE_UNKNOWN
    assert (
        hass.states.get("sensor.mycontroller_door1_temperature").state == STATE_UNKNOWN
    )

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert not hass.states.async_entity_ids(DOMAIN)