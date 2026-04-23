async def test_websocket(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_wled: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test WebSocket connection."""
    state = hass.states.get("light.wled_websocket")
    assert state
    assert state.state == STATE_ON

    # There is no Future in place yet...
    assert mock_wled.connect.call_count == 1
    assert mock_wled.listen.call_count == 1
    assert mock_wled.disconnect.call_count == 1

    connection_connected = asyncio.Future()
    connection_finished = asyncio.Future()

    async def connect(callback: Callable[[WLEDDevice], None]):
        connection_connected.set_result(callback)
        await connection_finished

    # Mock out wled.listen with a Future
    mock_wled.listen.side_effect = connect

    # Mock out the event bus
    mock_bus = MagicMock()
    hass.bus = mock_bus

    # Next refresh it should connect
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    callback = await connection_connected

    # Connected to WebSocket, disconnect not called
    # listening for Home Assistant to stop
    assert mock_wled.connect.call_count == 2
    assert mock_wled.listen.call_count == 2
    assert mock_wled.disconnect.call_count == 1
    assert mock_bus.async_listen_once.call_count == 1
    assert (
        mock_bus.async_listen_once.call_args_list[0][0][0] == EVENT_HOMEASSISTANT_STOP
    )
    assert (
        mock_bus.async_listen_once.call_args_list[0][0][1].__name__ == "close_websocket"
    )
    assert mock_bus.async_listen_once.return_value.call_count == 0

    # Send update from WebSocket
    updated_device = deepcopy(mock_wled.update.return_value)
    updated_device.state.on = False
    callback(updated_device)
    await hass.async_block_till_done()

    # Check if entity updated
    state = hass.states.get("light.wled_websocket")
    assert state
    assert state.state == STATE_OFF

    # Resolve Future with a connection losed.
    connection_finished.set_exception(WLEDConnectionClosedError)
    await hass.async_block_till_done()

    # Disconnect called, unsubbed Home Assistant stop listener
    assert mock_wled.disconnect.call_count == 2
    assert mock_bus.async_listen_once.return_value.call_count == 1

    # Light still available, as polling takes over
    state = hass.states.get("light.wled_websocket")
    assert state
    assert state.state == STATE_OFF