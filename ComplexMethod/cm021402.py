async def test_update_fail(
    hass: HomeAssistant,
    mock_bridge,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test entities state unavailable when updates fail.."""
    entry = await init_integration(hass)
    assert mock_bridge

    mock_bridge.mock_callbacks(DUMMY_SWITCHER_DEVICES)
    await hass.async_block_till_done()

    assert mock_bridge.is_running is True
    assert len(entry.runtime_data) == 2

    freezer.tick(timedelta(seconds=MAX_UPDATE_INTERVAL_SEC + 1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    for device in DUMMY_SWITCHER_DEVICES:
        assert (
            f"Device {device.name} did not send update for {MAX_UPDATE_INTERVAL_SEC} seconds"
            in caplog.text
        )

        entity_id = f"switch.{slugify(device.name)}"
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNAVAILABLE

        entity_id = f"sensor.{slugify(device.name)}_power"
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNAVAILABLE

    mock_bridge.mock_callbacks(DUMMY_SWITCHER_DEVICES)
    await hass.async_block_till_done()
    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=MAX_UPDATE_INTERVAL_SEC - 2)
    )
    await hass.async_block_till_done()

    for device in DUMMY_SWITCHER_DEVICES:
        entity_id = f"switch.{slugify(device.name)}"
        state = hass.states.get(entity_id)
        assert state.state != STATE_UNAVAILABLE

        entity_id = f"sensor.{slugify(device.name)}_power"
        state = hass.states.get(entity_id)
        assert state.state != STATE_UNAVAILABLE