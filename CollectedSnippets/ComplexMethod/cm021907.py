async def test_setup_and_remove_config_entry(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    tariffs: str,
    expected_entities: list[str],
) -> None:
    """Test setting up and removing a config entry."""
    input_sensor_entity_id = "sensor.input"

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": input_sensor_entity_id,
            "tariffs": tariffs,
        },
        title="Electricity meter",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == len(expected_entities)
    assert len(entity_registry.entities) == len(expected_entities)
    for entity in expected_entities:
        assert hass.states.get(entity)
        assert entity in entity_registry.entities

    # Remove the config entry
    assert await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the state and entity registry entry are removed
    assert len(hass.states.async_all()) == 0
    assert len(entity_registry.entities) == 0