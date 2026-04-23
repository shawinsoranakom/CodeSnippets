async def test_update_available(hass: HomeAssistant) -> None:
    """Test device has firmware update available."""

    update_firmware = AsyncMock()
    await setup_integration(hass, FIRMWARE_UPDATE_AVAILABLE, update_firmware)

    state = hass.states.get("update.friendly_name")

    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_DEVICE_CLASS] == UpdateDeviceClass.FIRMWARE
    assert state.attributes[ATTR_INSTALLED_VERSION] == "4.99.491"
    assert state.attributes[ATTR_LATEST_VERSION] == "4.100.502"
    assert (
        state.attributes[ATTR_RELEASE_URL]
        == "http://docs.linn.co.uk/wiki/index.php/ReleaseNotes"
    )
    assert (
        state.attributes[ATTR_RELEASE_SUMMARY]
        == "Release build version 4.100.502 (07 Jun 2023 12:29:48)"
    )

    await hass.services.async_call(
        UPDATE_DOMAIN,
        SERVICE_INSTALL,
        {ATTR_ENTITY_ID: "update.friendly_name"},
        blocking=True,
    )
    await hass.async_block_till_done()

    update_firmware.assert_called_once()