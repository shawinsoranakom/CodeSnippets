async def help_test_entity_debug_info_max_messages(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    domain: str,
    config: ConfigType,
) -> None:
    """Test debug_info message overflow.

    This is a test helper for MQTT debug_info.
    """
    await mqtt_mock_entry()
    # Add device settings to config
    config = copy.deepcopy(config[mqtt.DOMAIN][domain])
    config["device"] = copy.deepcopy(DEFAULT_CONFIG_DEVICE_INFO_ID)
    config["unique_id"] = "veryunique"

    registry = dr.async_get(hass)

    data = json.dumps(config)
    async_fire_mqtt_message(hass, f"homeassistant/{domain}/bla/config", data)
    await hass.async_block_till_done()

    device = registry.async_get_device(identifiers={("mqtt", "helloworld")})
    assert device is not None

    debug_info_data = debug_info.info_for_device(hass, device.id)
    assert len(debug_info_data["entities"][0]["subscriptions"]) == 1
    assert {"topic": "test-topic", "messages": []} in debug_info_data["entities"][0][
        "subscriptions"
    ]

    with freeze_time(start_dt := dt_util.utcnow()):
        for i in range(debug_info.STORED_MESSAGES + 1):
            async_fire_mqtt_message(hass, "test-topic", f"{i}")

        debug_info_data = debug_info.info_for_device(hass, device.id)

    assert len(debug_info_data["entities"][0]["subscriptions"]) == 1
    assert (
        len(debug_info_data["entities"][0]["subscriptions"][0]["messages"])
        == debug_info.STORED_MESSAGES
    )
    messages = [
        {
            "payload": f"{i}",
            "qos": 0,
            "retain": False,
            "time": start_dt,
            "topic": "test-topic",
        }
        for i in range(1, debug_info.STORED_MESSAGES + 1)
    ]
    assert {"topic": "test-topic", "messages": messages} in debug_info_data["entities"][
        0
    ]["subscriptions"]