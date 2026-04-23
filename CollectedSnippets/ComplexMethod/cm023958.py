async def test_service_get_queue_season_pack(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_sonarr_season_pack: MagicMock,
) -> None:
    """Test get_queue service with a season pack download."""
    # Set up integration with season pack queue data
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_QUEUE,
        {ATTR_ENTRY_ID: mock_config_entry.entry_id},
        blocking=True,
        return_response=True,
    )

    assert response is not None
    assert ATTR_SHOWS in response
    shows = response[ATTR_SHOWS]

    # Should have only 1 entry (the season pack) instead of 3 (one per episode)
    assert len(shows) == 1

    # Check the season pack data structure
    season_pack = shows["House.S02.1080p.BluRay.x264-SHORTBREHD"]
    assert season_pack["title"] == "House"
    assert season_pack["season_number"] == 2
    assert season_pack["download_title"] == "House.S02.1080p.BluRay.x264-SHORTBREHD"

    # Check season pack specific fields
    assert season_pack["is_season_pack"] is True
    assert season_pack["episode_count"] == 3  # Episodes 1, 2, and 24 in fixture
    assert season_pack["episode_range"] == "E01-E24"
    assert season_pack["episode_identifier"] == "S02 (3 episodes)"

    # Check that basic download info is still present
    assert season_pack["size"] == 84429221268
    assert season_pack["status"] == "paused"
    assert season_pack["quality"] == "Bluray-1080p"