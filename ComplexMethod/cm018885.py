async def test_update_refresh_token_api_error(
    hass: HomeAssistant,
    mock_nice_go: AsyncMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test updating refresh token with error."""

    await setup_integration(hass, mock_config_entry, [Platform.COVER])

    assert mock_nice_go.authenticate_refresh.call_count == 1
    assert mock_nice_go.get_all_barriers.call_count == 1
    assert mock_nice_go.authenticate.call_count == 0

    mock_nice_go.authenticate.side_effect = ApiError
    freezer.tick(timedelta(days=30))
    async_fire_time_changed(hass)
    assert not await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_nice_go.authenticate_refresh.call_count == 1
    assert mock_nice_go.authenticate.call_count == 1
    assert mock_nice_go.get_all_barriers.call_count == 1
    assert mock_config_entry.data["refresh_token"] == "test-refresh-token"
    assert "API error" in caplog.text