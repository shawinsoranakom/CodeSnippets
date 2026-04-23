async def help_test_entity_debug_info_message(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    domain: str,
    config: ConfigType,
    service: str | None,
    command_topic: str | None = None,
    command_payload: str | None = None,
    state_topic: str | object | None = _SENTINEL,
    state_payload: bytes | str | None = None,
    service_parameters: dict[str, Any] | None = None,
) -> None:
    """Test debug_info.

    This is a test helper for MQTT debug_info.
    """
    # Add device settings to config
    await mqtt_mock_entry()
    config = copy.deepcopy(config[mqtt.DOMAIN][domain])
    config["device"] = copy.deepcopy(DEFAULT_CONFIG_DEVICE_INFO_ID)
    config["unique_id"] = "veryunique"

    if command_topic is None:
        # Add default topic to config
        config["command_topic"] = "command-topic"
        command_topic = "command-topic"

    if command_payload is None:
        command_payload = "ON"

    if state_topic is _SENTINEL:
        # Add default topic to config
        config["state_topic"] = "state-topic"
        state_topic = "state-topic"

    if state_payload is None:
        state_payload = "ON"

    registry = dr.async_get(hass)

    data = json.dumps(config)
    async_fire_mqtt_message(hass, f"homeassistant/{domain}/bla/config", data)
    await hass.async_block_till_done()

    device = registry.async_get_device(identifiers={("mqtt", "helloworld")})
    assert device is not None

    debug_info_data = debug_info.info_for_device(hass, device.id)

    if state_topic is not None:
        assert len(debug_info_data["entities"][0]["subscriptions"]) >= 1
        assert {"topic": state_topic, "messages": []} in debug_info_data["entities"][0][
            "subscriptions"
        ]

        with freeze_time(start_dt := dt_util.utcnow()):
            async_fire_mqtt_message(hass, str(state_topic), state_payload)

            debug_info_data = debug_info.info_for_device(hass, device.id)
            assert len(debug_info_data["entities"][0]["subscriptions"]) >= 1
            assert {
                "topic": state_topic,
                "messages": [
                    {
                        "payload": str(state_payload),
                        "qos": 0,
                        "retain": False,
                        "time": start_dt,
                        "topic": state_topic,
                    }
                ],
            } in debug_info_data["entities"][0]["subscriptions"]

    expected_transmissions = []

    with freeze_time(start_dt := dt_util.utcnow()):
        if service:
            # Trigger an outgoing MQTT message
            if service:
                service_data = {ATTR_ENTITY_ID: f"{domain}.beer_test"}
                if service_parameters:
                    service_data.update(service_parameters)

                await hass.services.async_call(
                    domain,
                    service,
                    service_data,
                    blocking=True,
                )

            expected_transmissions = [
                {
                    "topic": command_topic,
                    "messages": [
                        {
                            "payload": str(command_payload),
                            "qos": 0,
                            "retain": False,
                            "time": start_dt,
                            "topic": command_topic,
                        }
                    ],
                }
            ]

        debug_info_data = debug_info.info_for_device(hass, device.id)
        assert debug_info_data["entities"][0]["transmitted"] == expected_transmissions