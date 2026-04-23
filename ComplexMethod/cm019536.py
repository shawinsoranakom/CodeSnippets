async def test_light_update(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_hub_ping: AsyncMock,
    mock_hub_configuration_prod_awning_dimmer: AsyncMock,
    mock_hub_status_prod_dimmer: AsyncMock,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that a light entity is created and updated correctly."""
    assert await setup_config_entry(hass, mock_config_entry)
    assert len(mock_hub_ping.mock_calls) == 1
    assert len(mock_hub_configuration_prod_awning_dimmer.mock_calls) == 1
    assert len(mock_hub_status_prod_dimmer.mock_calls) == 2

    entity = hass.states.get("light.licht")
    assert entity is not None
    assert entity == snapshot

    # Move time to next update
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert len(mock_hub_status_prod_dimmer.mock_calls) >= 3