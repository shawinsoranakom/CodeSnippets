async def test_select_becomes_unavailable_when_profiles_removed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_openrgb_client: MagicMock,
    mock_profiles: list[SimpleNamespace],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test select becomes unavailable when all profiles are removed."""
    # Start with profiles
    mock_openrgb_client.profiles = mock_profiles

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    # Verify select entity is available with profiles
    state = hass.states.get("select.test_computer_profile")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.attributes.get("options") == ["Gaming", "Work", "Rainbow"]

    # Remove all profiles
    mock_openrgb_client.profiles = []

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Verify select entity becomes unavailable
    state = hass.states.get("select.test_computer_profile")
    assert state
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes.get("options") == []