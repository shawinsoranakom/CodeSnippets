async def test_energy_refresh_token_expired_recovery(
    hass: HomeAssistant,
    normal_config_entry: MockConfigEntry,
    mock_live_status: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test energy coordinator recovers from expired access token."""
    await setup_platform(hass, normal_config_entry)
    assert normal_config_entry.state is ConfigEntryState.LOADED
    assert (state := hass.states.get("sensor.energy_site_grid_power"))
    assert state.state != "unavailable"

    mock_live_status.reset_mock()
    mock_live_status.side_effect = OAuthExpired

    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert normal_config_entry.state is ConfigEntryState.LOADED
    assert (state := hass.states.get("sensor.energy_site_grid_power"))
    assert state.state == "unavailable"
    assert normal_config_entry.data["token"]["expires_at"] == 0
    assert mock_live_status.call_count == 1

    mock_live_status.side_effect = None
    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get("sensor.energy_site_grid_power"))
    assert state.state != "unavailable"
    assert mock_live_status.call_count == 2