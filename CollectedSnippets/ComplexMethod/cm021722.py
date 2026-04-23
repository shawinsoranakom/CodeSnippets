async def test_handle_cleanup_exception(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    mock_imap_protocol: MagicMock,
    imap_close: Exception,
) -> None:
    """Test handling an excepton during cleaning up."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    # Make sure we have had one update (when polling)
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=5))
    await hass.async_block_till_done()

    state = hass.states.get("sensor.imap_email_email_com_messages")
    # we should have an entity
    assert state is not None
    assert state.state == "0"

    # Fail cleaning up
    mock_imap_protocol.close.side_effect = imap_close

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert "Error while cleaning up imap connection" in caplog.text

    state = hass.states.get("sensor.imap_email_email_com_messages")

    # we should have an entity with an unavailable state
    assert state is not None
    assert state.state == STATE_UNAVAILABLE