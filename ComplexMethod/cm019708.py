async def test_switch_restore_state(
    hass: HomeAssistant,
    switch_config_entry: ConfigEntry,
    mock_firmware_client,
    initial_state: str,
    expected_state: str,
    expected_prerelease: bool,
) -> None:
    """Test switch restores previous state and has correct entity attributes."""
    mock_restore_cache(hass, [State(TEST_SWITCH_ENTITY_ID, initial_state)])

    assert await hass.config_entries.async_setup(switch_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_SWITCH_ENTITY_ID)
    assert state is not None
    assert state.state == expected_state
    assert state.attributes.get("friendly_name") == "Mock Device Beta firmware updates"

    # Verify coordinator was called with correct value during setup
    assert mock_firmware_client.update_prerelease.mock_calls == [
        call(expected_prerelease)
    ]

    # Verify entity registry attributes
    entity_registry = er.async_get(hass)
    entity_entry = entity_registry.async_get(TEST_SWITCH_ENTITY_ID)
    assert entity_entry is not None
    assert entity_entry.entity_category == EntityCategory.CONFIG
    assert entity_entry.translation_key == "beta_firmware"