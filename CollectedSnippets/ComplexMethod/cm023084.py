async def test_start_addon_redacts_set_options_error(
    hass: HomeAssistant,
    install_addon: AsyncMock,
    set_addon_options: AsyncMock,
    start_addon: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test startup redacts add-on options backend error details."""
    device = "/test"
    secret = TEST_SENSITIVE_NETWORK_KEY
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Z-Wave JS",
        data={"use_addon": True, "usb_path": device, "network_key": secret},
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert install_addon.call_count == 0
    assert set_addon_options.call_count == 1
    assert start_addon.call_count == 0
    assert "Failed to set the Z-Wave JS app options" in caplog.text
    assert "not a valid value for dictionary value" in caplog.text
    assert REDACTED in caplog.text
    assert secret not in caplog.text