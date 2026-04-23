async def test_loading_subentries(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    mqtt_config_subentries_data: tuple[dict[str, Any]],
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test loading subentries."""
    await mqtt_mock_entry()
    entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    subentry_id = next(iter(entry.subentries))
    # Each subentry has one device
    device = device_registry.async_get_device({("mqtt", subentry_id)})
    assert device is not None
    for object_id, component in mqtt_config_subentries_data[0]["data"][
        "components"
    ].items():
        platform = component["platform"]
        entity_id = f"{platform}.{slugify(device.name)}_{slugify(component['name'])}"
        entity_entry_entity_id = entity_registry.async_get_entity_id(
            platform, mqtt.DOMAIN, f"{subentry_id}_{object_id}"
        )
        assert entity_entry_entity_id == entity_id
        state = hass.states.get(entity_id)
        assert state is not None
        assert (
            state.attributes.get("entity_picture") == f"https://example.com/{object_id}"
        )
        # Availability was configured, so entities are unavailable
        assert state.state == "unavailable"

    # Make entities available
    async_fire_mqtt_message(hass, "test/availability", '{"availability": "online"}')
    for component in mqtt_config_subentries_data[0]["data"]["components"].values():
        platform = component["platform"]
        entity_id = f"{platform}.{slugify(device.name)}_{slugify(component['name'])}"
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == "unknown"