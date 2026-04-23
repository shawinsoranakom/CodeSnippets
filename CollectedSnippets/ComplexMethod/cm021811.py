async def test_state(hass: HomeAssistant, mock_socket, now) -> None:
    """Check the state and update of the binary sensor."""
    mock_socket.recv.return_value = b"off"
    assert await async_setup_component(hass, "binary_sensor", TEST_CONFIG)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY)

    assert state
    assert state.state == STATE_OFF
    assert mock_socket.connect.called
    assert mock_socket.connect.call_args == call(
        (BINARY_SENSOR_CONFIG["host"], BINARY_SENSOR_CONFIG["port"])
    )
    assert mock_socket.send.called
    assert mock_socket.send.call_args == call(BINARY_SENSOR_CONFIG["payload"].encode())
    assert mock_socket.recv.called
    assert mock_socket.recv.call_args == call(BINARY_SENSOR_CONFIG["buffer_size"])

    mock_socket.recv.return_value = b"on"

    async_fire_time_changed(hass, now + timedelta(seconds=45))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(TEST_ENTITY)

    assert state
    assert state.state == STATE_ON