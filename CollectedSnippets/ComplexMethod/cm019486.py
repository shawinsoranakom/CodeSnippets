async def test_coordinator_general_error(
    hass: HomeAssistant,
    mock_mastodon_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test general error during coordinator update makes entities unavailable."""
    await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    state = hass.states.get("binary_sensor.mastodon_trwnh_mastodon_social_bot")
    assert state is not None
    assert state.state == STATE_ON

    mock_mastodon_client.account_verify_credentials.side_effect = MastodonError

    freezer.tick(timedelta(hours=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    state = hass.states.get("binary_sensor.mastodon_trwnh_mastodon_social_bot")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # No reauth flow should be triggered (unlike auth errors)
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 0