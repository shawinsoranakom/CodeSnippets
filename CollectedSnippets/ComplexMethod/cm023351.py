async def test_load_unload(
    hass: HomeAssistant,
    mock_meater_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test unload of Meater integration."""
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert (
        len(
            er.async_entries_for_config_entry(
                entity_registry, mock_config_entry.entry_id
            )
        )
        == 8
    )
    assert (
        hass.states.get("sensor.meater_probe_40a72384_ambient_temperature").state
        != STATE_UNAVAILABLE
    )

    assert await hass.config_entries.async_reload(mock_config_entry.entry_id)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert (
        len(
            er.async_entries_for_config_entry(
                entity_registry, mock_config_entry.entry_id
            )
        )
        == 8
    )
    assert (
        hass.states.get("sensor.meater_probe_40a72384_ambient_temperature").state
        != STATE_UNAVAILABLE
    )