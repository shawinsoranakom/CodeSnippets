async def test_update_refresh_token(
    hass: HomeAssistant,
    mock_nice_go: AsyncMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test updating refresh token."""

    await setup_integration(hass, mock_config_entry, [Platform.COVER])

    assert mock_nice_go.authenticate_refresh.call_count == 1
    assert mock_nice_go.get_all_barriers.call_count == 1
    assert mock_nice_go.authenticate.call_count == 0

    mock_nice_go.authenticate.return_value = "new-refresh-token"
    freezer.tick(timedelta(days=30, seconds=1))
    async_fire_time_changed(hass)
    assert await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_nice_go.authenticate_refresh.call_count == 1
    assert mock_nice_go.authenticate.call_count == 1
    assert mock_nice_go.get_all_barriers.call_count == 2
    assert mock_config_entry.data["refresh_token"] == "new-refresh-token"