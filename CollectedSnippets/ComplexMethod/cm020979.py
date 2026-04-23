async def test_on_latest_firmware(hass: HomeAssistant) -> None:
    """Test device on latest firmware."""

    update_firmware = AsyncMock()
    await setup_integration(hass, LATEST_FIRMWARE_INSTALLED, update_firmware)

    state = hass.states.get("update.friendly_name")

    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_DEVICE_CLASS] == UpdateDeviceClass.FIRMWARE
    assert state.attributes[ATTR_INSTALLED_VERSION] == "4.100.502"
    assert state.attributes[ATTR_LATEST_VERSION] is None
    assert state.attributes[ATTR_RELEASE_URL] is None
    assert state.attributes[ATTR_RELEASE_SUMMARY] is None
    update_firmware.assert_not_called()