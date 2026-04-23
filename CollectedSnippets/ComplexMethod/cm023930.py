async def test_sensors(
    hass: HomeAssistant,
    mqtt_mock: MqttMockHAClient,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    config_entry: MockConfigEntry,
    topic: str,
    reset: str,
    data: str,
) -> None:
    """Test DROP sensors."""
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.drop_connect.PLATFORMS", [Platform.BINARY_SENSOR]
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    entity_entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )

    assert entity_entries
    for entity_entry in entity_entries:
        assert hass.states.get(entity_entry.entity_id).state == STATE_OFF

    async_fire_mqtt_message(hass, topic, reset)
    await hass.async_block_till_done()

    entity_entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )

    assert entity_entries
    for entity_entry in entity_entries:
        assert hass.states.get(entity_entry.entity_id).state == STATE_OFF

    async_fire_mqtt_message(hass, topic, data)
    await hass.async_block_till_done()

    entity_entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )
    assert entity_entries
    for entity_entry in entity_entries:
        assert entity_entry == snapshot(name=f"{entity_entry.entity_id}-entry")
        assert hass.states.get(entity_entry.entity_id) == snapshot(
            name=f"{entity_entry.entity_id}-state"
        )