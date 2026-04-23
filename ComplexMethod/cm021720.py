async def test_receiving_message_with_invalid_encoding(
    hass: HomeAssistant, mock_imap_protocol: MagicMock
) -> None:
    """Test receiving a message successfully."""
    event_called = async_capture_events(hass, "imap_content")

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    # Make sure we have had one update (when polling)
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=5))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.imap_email_email_com_messages")
    # we should have received one message
    assert state is not None
    assert state.state == "1"
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT

    # we should have received one event
    assert len(event_called) == 1
    data: dict[str, Any] = event_called[0].data
    assert data["server"] == "imap.server.com"
    assert data["username"] == "email@email.com"
    assert data["search"] == "UnSeen UnDeleted"
    assert data["folder"] == "INBOX"
    assert data["sender"] == "john.doe@example.com"
    assert data["subject"] == "Test subject"
    assert data["text"] == TEST_BADLY_ENCODED_CONTENT
    assert data["uid"] == "1"