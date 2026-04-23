async def test_update_entity_state_restoration(
    hass: HomeAssistant, update_config_entry: ConfigEntry
) -> None:
    """Test the Hardware firmware update entity state restoration."""

    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(TEST_UPDATE_ENTITY_ID, "on"),
                FirmwareUpdateExtraStoredData(
                    firmware_manifest=TEST_MANIFEST
                ).as_dict(),
            )
        ],
    )

    assert await hass.config_entries.async_setup(update_config_entry.entry_id)
    await hass.async_block_till_done()

    # The state is correctly restored
    state = hass.states.get(TEST_UPDATE_ENTITY_ID)
    assert state is not None
    assert state.state == "on"
    assert state.attributes["title"] == "EmberZNet"
    assert state.attributes["installed_version"] == "7.3.1.0"
    assert state.attributes["latest_version"] == "7.4.4.0"
    assert state.attributes["release_summary"] == ("Some release notes go here")
    assert state.attributes["release_url"] == ("https://example.org/release_notes")