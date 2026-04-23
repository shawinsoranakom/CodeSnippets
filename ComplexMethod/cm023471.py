async def test_websocket_watchdog(
    hass: HomeAssistant,
    mock_automower_client,
    mock_config_entry,
    freezer: FrozenDateTimeFactory,
    entity_registry: er.EntityRegistry,
    values: dict[str, MowerAttributes],
) -> None:
    """Test that the ws_ready_callback triggers an attempt to start the Watchdog task.

    and that the pong callback stops polling when all mowers are inactive.
    """
    poll_values = deepcopy(values)
    callback_holder: dict[str, Callable] = {}

    @callback
    def fake_register_websocket_response(
        cb: Callable[[dict[str, MowerAttributes]], None],
    ) -> None:
        callback_holder["data_cb"] = cb

    mock_automower_client.register_data_callback.side_effect = (
        fake_register_websocket_response
    )
    ws_ready_callbacks: list[Callable[[], None]] = []

    @callback
    def fake_register_ws_ready_callback(cb: Callable[[], None]) -> None:
        ws_ready_callbacks.append(cb)

    mock_automower_client.register_ws_ready_callback.side_effect = (
        fake_register_ws_ready_callback
    )

    await setup_integration(hass, mock_config_entry)

    for cb in ws_ready_callbacks:
        cb()

    await hass.async_block_till_done()
    assert mock_automower_client.get_status.call_count == 1

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert mock_automower_client.get_status.call_count == 2

    # websocket is still active, but mowers are inactive -> no polling required
    poll_values[TEST_MOWER_ID].mower.state = MowerStates.OFF
    poll_values["1234"].mower.state = MowerStates.OFF

    mock_automower_client.get_status.return_value = poll_values
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert mock_automower_client.get_status.call_count == 3

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert mock_automower_client.get_status.call_count == 4

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert mock_automower_client.get_status.call_count == 4

    # Simulate Pong loss and reset mock -> polling required
    mock_automower_client.send_empty_message.return_value = False
    mock_automower_client.get_status.reset_mock()

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert mock_automower_client.get_status.call_count == 0

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert mock_automower_client.get_status.call_count == 1

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert mock_automower_client.get_status.call_count == 2