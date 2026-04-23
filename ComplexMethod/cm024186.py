async def test_discovery_with_late_via_device_update(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    tag_mock: AsyncMock,
    single_configs: list[tuple[str, dict[str, Any]]],
) -> None:
    """Test a via device is available and the discovery of the via device is is set via an update."""
    await mqtt_mock_entry()

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    via_device_entry = device_registry.async_get_device(
        {("mqtt", "id_via_very_unique")}
    )
    assert via_device_entry is None
    # Discovery single config schema without via device
    for discovery_topic, config in single_configs:
        payload = json.dumps(config)
        async_fire_mqtt_message(
            hass,
            discovery_topic,
            payload,
        )
        via_device_entry = device_registry.async_get_device(
            {("mqtt", "id_via_very_unique")}
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
        assert via_device_entry is None

    # Resend the discovery update to set the via device
    for discovery_topic, config in single_configs:
        config["device"]["via_device"] = "id_via_very_unique"
        payload = json.dumps(config)
        async_fire_mqtt_message(
            hass,
            discovery_topic,
            payload,
        )
        via_device_entry = device_registry.async_get_device(
            {("mqtt", "id_via_very_unique")}
        )
        assert via_device_entry is not None
        assert via_device_entry.name is None

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Now discover the via device (a switch)
    via_device_config = {
        "name": None,
        "command_topic": "test-switch-topic",
        "unique_id": "very_unique_switch",
        "device": {"identifiers": ["id_via_very_unique"], "name": "My Switch"},
    }
    payload = json.dumps(via_device_config)
    via_device_discovery_topic = "homeassistant/switch/very_unique/config"
    async_fire_mqtt_message(
        hass,
        via_device_discovery_topic,
        payload,
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    via_device_entry = device_registry.async_get_device(
        {("mqtt", "id_via_very_unique")}
    )
    assert via_device_entry is not None
    assert via_device_entry.name == "My Switch"

    await help_check_discovered_items(hass, device_registry, tag_mock)