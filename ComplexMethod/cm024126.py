async def test_debug_info_qos_retain(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test debug info."""
    await mqtt_mock_entry()
    config = {
        "device": {"identifiers": ["helloworld"]},
        "name": "test",
        "state_topic": "sensor/#",
        "unique_id": "veryunique",
    }

    data = json.dumps(config)
    async_fire_mqtt_message(hass, "homeassistant/sensor/bla/config", data)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={("mqtt", "helloworld")})
    assert device is not None

    debug_info_data = debug_info.info_for_device(hass, device.id)
    assert len(debug_info_data["entities"][0]["subscriptions"]) >= 1
    assert {"topic": "sensor/#", "messages": []} in debug_info_data["entities"][0][
        "subscriptions"
    ]

    start_dt = datetime(2019, 1, 1, 0, 0, 0, tzinfo=dt_util.UTC)
    freezer.move_to(start_dt)
    # simulate the first message was replayed from the broker with retained flag
    async_fire_mqtt_message(hass, "sensor/abc", "123", qos=0, retain=True)
    # simulate an update message
    async_fire_mqtt_message(hass, "sensor/abc", "123", qos=0, retain=False)
    # simpulate someone else subscribed and retained messages were replayed
    async_fire_mqtt_message(hass, "sensor/abc", "123", qos=1, retain=True)
    # simulate an update message
    async_fire_mqtt_message(hass, "sensor/abc", "123", qos=1, retain=False)
    # simulate an update message
    async_fire_mqtt_message(hass, "sensor/abc", "123", qos=2, retain=False)

    debug_info_data = debug_info.info_for_device(hass, device.id)
    assert len(debug_info_data["entities"][0]["subscriptions"]) == 1
    # The replayed retained payload was processed
    messages = debug_info_data["entities"][0]["subscriptions"][0]["messages"]
    assert {
        "payload": "123",
        "qos": 0,
        "retain": True,
        "time": start_dt,
        "topic": "sensor/abc",
    } in messages
    # The not retained update was processed normally
    assert {
        "payload": "123",
        "qos": 0,
        "retain": False,
        "time": start_dt,
        "topic": "sensor/abc",
    } in messages
    # Since the MQTT client has not lost the connection and has not resubscribed
    # The retained payload is not replayed and filtered out as it already
    # received a value and appears to be received on an existing subscription
    assert {
        "payload": "123",
        "qos": 1,
        "retain": True,
        "time": start_dt,
        "topic": "sensor/abc",
    } not in messages
    # The not retained update was processed normally
    assert {
        "payload": "123",
        "qos": 1,
        "retain": False,
        "time": start_dt,
        "topic": "sensor/abc",
    } in messages
    # The not retained update was processed normally
    assert {
        "payload": "123",
        "qos": 2,
        "retain": False,
        "time": start_dt,
        "topic": "sensor/abc",
    } in messages