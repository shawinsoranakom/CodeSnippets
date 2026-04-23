async def test_trophy_title_coordinator_play_new_game(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_psnawpapi: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test we play a new game and get a title image on next trophy titles update."""

    _tmp = mock_psnawpapi.user.return_value.trophy_titles.return_value
    mock_psnawpapi.user.return_value.trophy_titles.return_value = []

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    assert len(mock_psnawpapi.user.return_value.trophy_titles.mock_calls) == 1

    assert (state := hass.states.get("media_player.playstation_vita"))
    assert state.attributes.get("entity_picture") is None

    mock_psnawpapi.user.return_value.trophy_titles.return_value = _tmp

    # Wait one day to trigger PlaystationNetworkTrophyTitlesCoordinator refresh
    freezer.tick(timedelta(days=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Wait another 30 seconds in case the PlaystationNetworkUserDataCoordinator,
    # which has a 30 second update interval, updated before the
    # PlaystationNetworkTrophyTitlesCoordinator.
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert len(mock_psnawpapi.user.return_value.trophy_titles.mock_calls) == 2

    assert (state := hass.states.get("media_player.playstation_vita"))
    assert (
        state.attributes["entity_picture"]
        == "https://image.api.playstation.com/trophy/np/NPWR03134_00_0008206095F67FD3BB385E9E00A7C9CFE6F5A4AB96/5F87A6997DD23D1C4D4CC0D1F958ED79CB905331.PNG"
    )