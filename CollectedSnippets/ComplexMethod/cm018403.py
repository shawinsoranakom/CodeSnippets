async def test_event_updates_state(
    hass: HomeAssistant,
    mock_transmission_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    hass_event: str,
    expected_event_type: str,
) -> None:
    """Test Transmission events update the entity state and attributes."""
    with patch("homeassistant.components.transmission.PLATFORMS", [Platform.EVENT]):
        await setup_integration(hass, mock_config_entry)
        await hass.async_block_till_done()

    client = mock_transmission_client.return_value
    torrent_status = {
        EVENT_TYPE_STARTED: "downloading",
        EVENT_TYPE_DOWNLOADED: "seeding",
        EVENT_TYPE_REMOVED: "stopped",
    }[hass_event]
    torrent = SimpleNamespace(
        id=1,
        name="Test",
        status=torrent_status,
        download_dir="/downloads",
        labels=[],
    )

    torrents_sequence = {
        EVENT_TYPE_STARTED: [[torrent]],
        EVENT_TYPE_DOWNLOADED: [[torrent]],
        EVENT_TYPE_REMOVED: [[torrent], []],
    }[hass_event]

    client.get_torrents.side_effect = torrents_sequence

    for _ in torrents_sequence:
        freezer.tick(timedelta(seconds=DEFAULT_SCAN_INTERVAL + 1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("event.transmission_torrent")
    assert state is not None
    assert state.attributes[ATTR_EVENT_TYPE] == expected_event_type
    assert state.attributes["id"] == 1
    assert state.attributes["name"] == "Test"
    assert state.attributes["download_path"] == "/downloads"
    assert state.attributes["labels"] == []
    assert dt_util.parse_datetime(state.state) is not None