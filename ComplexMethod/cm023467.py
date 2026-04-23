async def test_constant_polling(
    hass: HomeAssistant,
    mock_automower_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    values: dict[str, MowerAttributes],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Verify that receiving a WebSocket update does not interrupt the regular polling cycle.

    The test simulates a WebSocket update that changes an entity's state, then advances time
    to trigger a scheduled poll to confirm polled data also arrives.
    """
    test_values = deepcopy(values)
    callback_holder: dict[str, Callable] = {}

    @callback
    def fake_register_websocket_response(
        cb: Callable[[dict[str, MowerAttributes]], None],
    ) -> None:
        callback_holder["cb"] = cb

    mock_automower_client.register_data_callback.side_effect = (
        fake_register_websocket_response
    )
    await setup_integration(hass, mock_config_entry)
    await hass.async_block_till_done()

    assert mock_automower_client.register_data_callback.called
    assert "cb" in callback_holder

    state = hass.states.get("sensor.test_mower_1_battery")
    assert state is not None
    assert state.state == "100"
    state = hass.states.get("sensor.test_mower_1_front_lawn_progress")
    assert state is not None
    assert state.state == "40"

    test_values[TEST_MOWER_ID].battery.battery_percent = 77

    freezer.tick(SCAN_INTERVAL - timedelta(seconds=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    callback_holder["cb"](test_values)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_mower_1_battery")
    assert state is not None
    assert state.state == "77"
    state = hass.states.get("sensor.test_mower_1_front_lawn_progress")
    assert state is not None
    assert state.state == "40"

    test_values[TEST_MOWER_ID].work_areas[123456].progress = 50
    mock_automower_client.get_status.return_value = test_values
    freezer.tick(timedelta(seconds=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    mock_automower_client.get_status.assert_awaited()
    state = hass.states.get("sensor.test_mower_1_battery")
    assert state is not None
    assert state.state == "77"
    state = hass.states.get("sensor.test_mower_1_front_lawn_progress")
    assert state is not None
    assert state.state == "50"