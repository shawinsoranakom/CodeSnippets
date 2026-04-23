async def test_season_northern_hemisphere(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    type: str,
    day: datetime,
    expected: str,
) -> None:
    """Test that season should be summer."""
    hass.config.latitude = HEMISPHERE_NORTHERN["homeassistant"]["latitude"]
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, unique_id=type, data={CONF_TYPE: type}
    )

    with freeze_time(day):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.season")
    assert state
    assert state.state == expected
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENUM
    assert state.attributes[ATTR_OPTIONS] == ["spring", "summer", "autumn", "winter"]

    entry = entity_registry.async_get("sensor.season")
    assert entry
    assert entry.unique_id == mock_config_entry.entry_id
    assert entry.translation_key == "season"