async def test_async_setup_entry_loads_platforms(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    controller: MockHeos,
) -> None:
    """Test load connects to heos, retrieves players, and loads platforms."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get("media_player.test_player") is not None
    assert controller.connect.call_count == 1
    assert controller.get_players.call_count == 1
    assert controller.get_favorites.call_count == 1
    assert controller.get_input_sources.call_count == 1
    controller.disconnect.assert_not_called()