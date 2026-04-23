async def help_test_entity_debug_info_remove(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    domain: str,
    config: ConfigType,
) -> None:
    """Test debug_info.

    This is a test helper for MQTT debug_info.
    """
    await mqtt_mock_entry()
    # Add device settings to config
    config = copy.deepcopy(config[mqtt.DOMAIN][domain])
    config["device"] = copy.deepcopy(DEFAULT_CONFIG_DEVICE_INFO_ID)
    config["unique_id"] = "veryunique"
    config["platform"] = "mqtt"

    registry = dr.async_get(hass)

    data = json.dumps(config)
    async_fire_mqtt_message(hass, f"homeassistant/{domain}/bla/config", data)
    await hass.async_block_till_done()

    device = registry.async_get_device(identifiers={("mqtt", "helloworld")})
    assert device is not None

    debug_info_data = debug_info.info_for_device(hass, device.id)
    assert len(debug_info_data["entities"]) == 1
    assert (
        debug_info_data["entities"][0]["discovery_data"]["topic"]
        == f"homeassistant/{domain}/bla/config"
    )
    assert debug_info_data["entities"][0]["discovery_data"]["payload"] == config
    assert len(debug_info_data["entities"][0]["subscriptions"]) == 1
    assert {"topic": "test-topic", "messages": []} in debug_info_data["entities"][0][
        "subscriptions"
    ]
    assert len(debug_info_data["triggers"]) == 0
    assert debug_info_data["entities"][0]["entity_id"] == f"{domain}.beer_test"
    entity_id = debug_info_data["entities"][0]["entity_id"]

    async_fire_mqtt_message(hass, f"homeassistant/{domain}/bla/config", "")
    await hass.async_block_till_done()

    debug_info_data = debug_info.info_for_device(hass, device.id)
    assert len(debug_info_data["entities"]) == 0
    assert len(debug_info_data["triggers"]) == 0
    assert entity_id not in hass.data["mqtt"].debug_info_entities