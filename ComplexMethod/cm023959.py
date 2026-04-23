async def test_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    mock_sonarr: MagicMock,
) -> None:
    """Test the creation and values of the sensors."""
    sensors = {
        "commands": "sonarr_commands",
        "diskspace": "sonarr_disk_space",
        "queue": "sonarr_queue",
        "series": "sonarr_shows",
        "wanted": "sonarr_wanted",
    }

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    for unique, oid in sensors.items():
        entity = entity_registry.async_get(f"sensor.{oid}")
        assert entity
        assert entity.unique_id == f"{mock_config_entry.entry_id}_{unique}"

    state = hass.states.get("sensor.sonarr_commands")
    assert state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "commands"
    assert state.state == "2"

    state = hass.states.get("sensor.sonarr_disk_space")
    assert state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfInformation.GIGABYTES
    assert state.state == "263.10"

    state = hass.states.get("sensor.sonarr_queue")
    assert state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "episodes"
    assert state.state == "1"

    state = hass.states.get("sensor.sonarr_shows")
    assert state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "series"
    assert state.state == "1"

    state = hass.states.get("sensor.sonarr_upcoming")
    assert state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "episodes"
    assert state.state == "1"

    state = hass.states.get("sensor.sonarr_wanted")
    assert state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "episodes"
    assert state.state == "2"