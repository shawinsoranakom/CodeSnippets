async def test_update_state_save_and_restore(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    matter_client: MagicMock,
    check_node_update: AsyncMock,
    matter_node: MatterNode,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test latest update information is retained across reload/restart."""
    state = hass.states.get("update.mock_dimmable_light_firmware")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes.get("installed_version") == "v1.0"

    check_node_update.return_value = TEST_SOFTWARE_VERSION

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert matter_client.check_node_update.call_count == 2

    state = hass.states.get("update.mock_dimmable_light_firmware")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get("latest_version") == "v2.0"
    await hass.async_block_till_done()
    await async_mock_restore_state_shutdown_restart(hass)

    assert len(hass_storage[RESTORE_STATE_KEY]["data"]) == 1
    state = hass_storage[RESTORE_STATE_KEY]["data"][0]["state"]
    assert state["entity_id"] == "update.mock_dimmable_light_firmware"
    extra_data = hass_storage[RESTORE_STATE_KEY]["data"][0]["extra_data"]

    # Check that the extra data has the format we expect.
    assert extra_data == {
        "software_update": {
            "vid": 65521,
            "pid": 32768,
            "software_version": 2,
            "software_version_string": "v2.0",
            "firmware_information": "",
            "min_applicable_software_version": 0,
            "max_applicable_software_version": 1,
            "release_notes_url": "http://home-assistant.io/non-existing-product",
            "update_source": "local",
        }
    }