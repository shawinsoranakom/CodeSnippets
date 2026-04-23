async def test_reset_last_message(
    hass: HomeAssistant,
    mock_imap_protocol: MagicMock,
    valid_date: bool,
    empty_search_reponse: tuple[str, list[bytes]],
) -> None:
    """Test receiving a message successfully."""
    event = asyncio.Event()  # needed for pushed coordinator to make a new loop
    idle_start_future = asyncio.Future()
    idle_start_future.set_result(None)

    async def _sleep_till_event() -> None:
        """Simulate imap server waiting for pushes message and keep the push loop going.

        Needed for pushed coordinator only.
        """
        nonlocal event
        await event.wait()
        event.clear()
        mock_imap_protocol.idle_start = AsyncMock(return_value=idle_start_future)

    # Make sure we make another cycle (needed for pushed coordinator)
    mock_imap_protocol.idle_start = AsyncMock(return_value=idle_start_future)
    # Mock we wait till we push an update (needed for pushed coordinator)
    mock_imap_protocol.wait_server_push.side_effect = _sleep_till_event

    event_called = async_capture_events(hass, "imap_content")

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    # Make sure we have had one update (when polling)
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=5))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.imap_email_email_com_messages")
    # We should have received one message
    assert state is not None
    assert state.state == "1"

    # We should have received one event
    assert len(event_called) == 1
    data: dict[str, Any] = event_called[0].data
    assert data["server"] == "imap.server.com"
    assert data["username"] == "email@email.com"
    assert data["search"] == "UnSeen UnDeleted"
    assert data["folder"] == "INBOX"
    assert data["sender"] == "john.doe@example.com"
    assert data["subject"] == "Test subject"
    assert data["text"]
    assert data["initial"]
    assert (valid_date and isinstance(data["date"], datetime)) or (
        not valid_date and data["date"] is None
    )

    # Simulate an update where no messages are found (needed for pushed coordinator)
    mock_imap_protocol.search.return_value = Response(*empty_search_reponse)

    # Make sure we have an update
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))

    # Awake loop (needed for pushed coordinator)
    event.set()

    await hass.async_block_till_done()

    state = hass.states.get("sensor.imap_email_email_com_messages")
    # We should have message
    assert state is not None
    assert state.state == "0"
    # No new events should be called
    assert len(event_called) == 1

    # Simulate an update where with the original message
    mock_imap_protocol.search.return_value = Response(*TEST_SEARCH_RESPONSE)
    # Make sure we have an update again with the same UID
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))

    # Awake loop (needed for pushed coordinator)
    event.set()

    await hass.async_block_till_done()

    state = hass.states.get("sensor.imap_email_email_com_messages")
    # We should have received one message
    assert state is not None
    assert state.state == "1"
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # One new event
    assert len(event_called) == 2