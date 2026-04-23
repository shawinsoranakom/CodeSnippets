async def test_block_sleeping_device_connection_error(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
    mock_block_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test block sleeping device connection error during initialize."""
    sleep_period = 1000
    entry = await init_integration(hass, 1, sleep_period=sleep_period, skip_setup=True)
    device = register_device(device_registry, entry)
    entity_id = register_entity(
        hass,
        BINARY_SENSOR_DOMAIN,
        "test_name_motion",
        "sensor_0-motion",
        entry,
        device_id=device.id,
    )
    mock_restore_cache(hass, [State(entity_id, STATE_ON)])
    monkeypatch.setattr(mock_block_device, "initialized", False)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    # Make device online event with connection error
    monkeypatch.setattr(
        mock_block_device,
        "initialize",
        AsyncMock(
            side_effect=DeviceConnectionError,
        ),
    )
    mock_block_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert "Error connecting to Shelly device" in caplog.text
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    # Move time to generate sleep period update
    freezer.tick(timedelta(seconds=sleep_period * UPDATE_PERIOD_MULTIPLIER))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert "Sleeping device did not update" in caplog.text
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNAVAILABLE