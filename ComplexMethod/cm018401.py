async def test_get_torrents_service(
    hass: HomeAssistant,
    mock_transmission_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_torrent,
    filter_mode: str,
    expected_statuses: list[str],
    expected_torrents: list[int],
) -> None:
    """Test get torrents service with various filter modes."""
    client = mock_transmission_client.return_value

    downloading_torrent = mock_torrent(torrent_id=1, name="Downloading", status=4)
    seeding_torrent = mock_torrent(torrent_id=2, name="Seeding", status=6)
    stopped_torrent = mock_torrent(torrent_id=3, name="Stopped", status=0)

    client.get_torrents.return_value = [
        downloading_torrent,
        seeding_torrent,
        stopped_torrent,
    ]

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_TORRENTS,
        {
            CONF_ENTRY_ID: mock_config_entry.entry_id,
            ATTR_TORRENT_FILTER: filter_mode,
        },
        blocking=True,
        return_response=True,
    )

    assert response is not None
    assert ATTR_TORRENTS in response
    torrents = response[ATTR_TORRENTS]
    assert isinstance(torrents, dict)

    assert len(torrents) == len(expected_statuses)

    for torrent_name, torrent_data in torrents.items():
        assert isinstance(torrent_data, dict)
        assert "id" in torrent_data
        assert "name" in torrent_data
        assert "status" in torrent_data
        assert torrent_data["name"] == torrent_name
        assert torrent_data["id"] in expected_torrents
        expected_torrents.remove(int(torrent_data["id"]))

    assert len(expected_torrents) == 0