async def help_test_entity_icon_and_entity_picture(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    domain: str,
    config: ConfigType,
) -> None:
    """Test entity picture and icon."""
    await mqtt_mock_entry()
    # Add device settings to config
    config = copy.deepcopy(config[mqtt.DOMAIN][domain])
    config["device"] = copy.deepcopy(DEFAULT_CONFIG_DEVICE_INFO_ID)

    ent_registry = er.async_get(hass)

    # Discover an entity without entity icon or picture
    unique_id = "veryunique1"
    config["unique_id"] = unique_id
    data = json.dumps(config)
    async_fire_mqtt_message(hass, f"homeassistant/{domain}/{unique_id}/config", data)
    await hass.async_block_till_done()
    entity_id = ent_registry.async_get_entity_id(domain, mqtt.DOMAIN, unique_id)
    state = hass.states.get(entity_id)
    assert entity_id is not None and state
    assert state.attributes.get("icon") is None
    assert state.attributes.get("entity_picture") is None

    # Discover an entity with an entity picture set
    unique_id = "veryunique2"
    config["entity_picture"] = "https://example.com/mypicture.png"
    config["unique_id"] = unique_id
    data = json.dumps(config)
    async_fire_mqtt_message(hass, f"homeassistant/{domain}/{unique_id}/config", data)
    await hass.async_block_till_done()
    entity_id = ent_registry.async_get_entity_id(domain, mqtt.DOMAIN, unique_id)
    state = hass.states.get(entity_id)
    assert entity_id is not None and state
    assert state.attributes.get("icon") is None
    assert state.attributes.get("entity_picture") == "https://example.com/mypicture.png"
    config.pop("entity_picture")

    # Discover an entity with an entity icon set
    unique_id = "veryunique3"
    config["icon"] = "mdi:emoji-happy-outline"
    config["unique_id"] = unique_id
    data = json.dumps(config)
    async_fire_mqtt_message(hass, f"homeassistant/{domain}/{unique_id}/config", data)
    await hass.async_block_till_done()
    entity_id = ent_registry.async_get_entity_id(domain, mqtt.DOMAIN, unique_id)
    state = hass.states.get(entity_id)
    assert entity_id is not None and state
    assert state.attributes.get("icon") == "mdi:emoji-happy-outline"
    assert state.attributes.get("entity_picture") is None