async def test_switch_update(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_hub_ping: AsyncMock,
    mock_hub_configuration_prod_load_switch: AsyncMock,
    mock_hub_status_prod_load_switch: AsyncMock,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that a switch entity is created and updated correctly."""
    assert await setup_config_entry(hass, mock_config_entry)
    assert len(mock_hub_ping.mock_calls) == 1
    assert len(mock_hub_configuration_prod_load_switch.mock_calls) == 1
    assert len(mock_hub_status_prod_load_switch.mock_calls) >= 2

    entity = hass.states.get("switch.heizung_links")
    assert entity is not None
    assert entity == snapshot

    before = len(mock_hub_status_prod_load_switch.mock_calls)

    # Move time to next update
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert len(mock_hub_status_prod_load_switch.mock_calls) > before