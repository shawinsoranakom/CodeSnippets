async def test_async_setup_entry_with_options_loads_platforms(
    hass: HomeAssistant,
    config_entry_options: MockConfigEntry,
    controller: MockHeos,
    new_mock: Mock,
) -> None:
    """Test load connects to heos with options, retrieves players, and loads platforms."""
    config_entry_options.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry_options.entry_id)

    # Assert options passed and methods called
    assert config_entry_options.state is ConfigEntryState.LOADED
    options = cast(HeosOptions, new_mock.call_args[0][0])
    assert options.host == config_entry_options.data[CONF_HOST]
    assert options.credentials is not None
    assert options.credentials.username == config_entry_options.options[CONF_USERNAME]
    assert options.credentials.password == config_entry_options.options[CONF_PASSWORD]
    assert controller.connect.call_count == 1
    assert controller.get_players.call_count == 1
    assert controller.get_favorites.call_count == 1
    assert controller.get_input_sources.call_count == 1
    controller.disconnect.assert_not_called()