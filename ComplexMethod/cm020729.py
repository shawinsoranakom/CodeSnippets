async def test_protection_window_recalculation(
    hass: HomeAssistant,
    config,
    config_entry,
    snapshot: SnapshotAssertion,
    set_time_zone,
    mock_pyopenuv,
    client,
    freezer: FrozenDateTimeFactory,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that protection window updates automatically without extra API calls."""

    freezer.move_to("2018-07-30T06:17:59-06:00")

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "binary_sensor.openuv_protection_window"
    state = hass.states.get(entity_id)
    assert state.state == "off"
    assert state == snapshot(name="before-protection-state")

    # move to when the protection window starts
    freezer.move_to("2018-07-30T09:17:59-06:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    entity_id = "binary_sensor.openuv_protection_window"
    state = hass.states.get(entity_id)
    assert state.state == "on"
    assert state == snapshot(name="during-protection-state")

    # move to when the protection window ends
    freezer.move_to("2018-07-30T16:47:59-06:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    entity_id = "binary_sensor.openuv_protection_window"
    state = hass.states.get(entity_id)
    assert state.state == "off"
    assert state == snapshot(name="after-protection-state")

    assert client.uv_protection_window.call_count == 1