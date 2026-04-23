async def test_update_refresh_token_auth_failed(
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

    mock_nice_go.authenticate.side_effect = AuthFailedError
    freezer.tick(timedelta(days=30))
    async_fire_time_changed(hass)
    assert not await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_nice_go.authenticate_refresh.call_count == 1
    assert mock_nice_go.authenticate.call_count == 1
    assert mock_nice_go.get_all_barriers.call_count == 1
    assert mock_config_entry.data["refresh_token"] == "test-refresh-token"
    assert "Authentication failed" in caplog.text
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    assert any(mock_config_entry.async_get_active_flows(hass, {SOURCE_REAUTH}))