async def test_update_entity_firmware_missing_from_manifest(
    hass: HomeAssistant, update_config_entry: ConfigEntry
) -> None:
    """Test the Hardware firmware update entity handles missing firmware."""

    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(TEST_UPDATE_ENTITY_ID, "on"),
                # Ensure the manifest does not contain our expected firmware type
                FirmwareUpdateExtraStoredData(
                    firmware_manifest=dataclasses.replace(TEST_MANIFEST, firmwares=())
                ).as_dict(),
            )
        ],
    )

    assert await hass.config_entries.async_setup(update_config_entry.entry_id)
    await hass.async_block_till_done()

    # The state is restored, accounting for the missing firmware
    state = hass.states.get(TEST_UPDATE_ENTITY_ID)
    assert state is not None
    assert state.state == "unknown"
    assert state.attributes["title"] == "EmberZNet"
    assert state.attributes["installed_version"] == "7.3.1.0"
    assert state.attributes["latest_version"] is None
    assert state.attributes["release_summary"] is None
    assert state.attributes["release_url"] is None