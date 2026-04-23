async def test_async_setup_no_internet(
    hass: HomeAssistant,
    mock_config_entry_host: MockConfigEntry,
    mock_smlight_client: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test we still load integration when no internet is available."""
    side_effect = mock_smlight_client.get_firmware_version.side_effect
    mock_smlight_client.get_firmware_version.side_effect = SmlightConnectionError

    await setup_integration(hass, mock_config_entry_host)

    entity = hass.states.get("update.mock_title_core_firmware")
    assert entity is not None
    assert entity.state == STATE_UNKNOWN

    freezer.tick(SCAN_FIRMWARE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    entity = hass.states.get("update.mock_title_core_firmware")
    assert entity is not None
    assert entity.state == STATE_UNKNOWN

    mock_smlight_client.get_firmware_version.side_effect = side_effect

    freezer.tick(SCAN_FIRMWARE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    entity = hass.states.get("update.mock_title_core_firmware")
    assert entity is not None
    assert entity.state == STATE_ON
    assert entity.attributes[ATTR_INSTALLED_VERSION] == "v2.3.6"