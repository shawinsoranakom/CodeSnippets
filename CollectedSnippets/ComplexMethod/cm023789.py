async def test_disabled_by_default_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    mock_charger: MagicMock,
) -> None:
    """Test the disabled by default sensor entities."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    state = hass.states.get("sensor.openevse_mock_config_ir_temperature")
    assert state is None

    entry = entity_registry.async_get("sensor.openevse_mock_config_ir_temperature")
    assert entry
    assert entry.disabled
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    state = hass.states.get("sensor.openevse_mock_config_rtc_temperature")
    assert state is None

    entry = entity_registry.async_get("sensor.openevse_mock_config_rtc_temperature")
    assert entry
    assert entry.disabled
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION