async def test_update_firm(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    reolink_host: MagicMock,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    entity_name: str,
) -> None:
    """Test update state when update available with firmware info from reolink.com."""
    reolink_host.sw_upload_progress.return_value = 100
    reolink_host.camera_sw_version.return_value = "v1.1.0.0.0.0000"
    new_firmware = NewSoftwareVersion(
        version_string="v3.3.0.226_23031644",
        download_url=TEST_DOWNLOAD_URL,
        release_notes=TEST_RELEASE_NOTES,
    )
    reolink_host.firmware_update_available.return_value = new_firmware

    with patch("homeassistant.components.reolink.PLATFORMS", [Platform.UPDATE]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    entity_id = f"{Platform.UPDATE}.{entity_name}_firmware"
    assert hass.states.get(entity_id).state == STATE_ON
    assert not hass.states.get(entity_id).attributes["in_progress"]
    assert hass.states.get(entity_id).attributes["update_percentage"] is None

    # release notes
    client = await hass_ws_client(hass)
    await hass.async_block_till_done()

    await client.send_json(
        {
            "id": 1,
            "type": "update/release_notes",
            "entity_id": entity_id,
        }
    )
    result = await client.receive_json()
    assert TEST_DOWNLOAD_URL in result["result"]
    assert TEST_RELEASE_NOTES in result["result"]

    # test install
    await hass.services.async_call(
        UPDATE_DOMAIN,
        SERVICE_INSTALL,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    reolink_host.update_firmware.assert_called()

    reolink_host.sw_upload_progress.return_value = 50
    freezer.tick(POLL_PROGRESS)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).attributes["in_progress"]
    assert hass.states.get(entity_id).attributes["update_percentage"] == 50

    reolink_host.sw_upload_progress.return_value = 100
    freezer.tick(POLL_AFTER_INSTALL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert not hass.states.get(entity_id).attributes["in_progress"]
    assert hass.states.get(entity_id).attributes["update_percentage"] is None

    reolink_host.update_firmware.side_effect = ReolinkError("Test error")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    reolink_host.update_firmware.side_effect = ApiError(
        "Test error", translation_key="firmware_rate_limit"
    )
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    # test _async_update_future
    reolink_host.camera_sw_version.return_value = "v3.3.0.226_23031644"
    reolink_host.firmware_update_available.return_value = False
    freezer.tick(POLL_AFTER_INSTALL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_OFF