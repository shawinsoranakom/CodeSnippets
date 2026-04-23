async def test_state(hass: HomeAssistant, mock_socket, mock_select) -> None:
    """Return the contents of _state."""
    assert await async_setup_component(hass, "sensor", TEST_CONFIG)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY)

    assert state
    assert state.state == "7.123"
    assert (
        state.attributes["unit_of_measurement"]
        == SENSOR_TEST_CONFIG[tcp.CONF_UNIT_OF_MEASUREMENT]
    )
    assert mock_socket.connect.called
    assert mock_socket.connect.call_args == call(
        (SENSOR_TEST_CONFIG["host"], SENSOR_TEST_CONFIG["port"])
    )
    assert mock_socket.send.called
    assert mock_socket.send.call_args == call(SENSOR_TEST_CONFIG["payload"].encode())
    assert mock_select.call_args == call(
        [mock_socket], [], [], SENSOR_TEST_CONFIG[tcp.CONF_TIMEOUT]
    )
    assert mock_socket.recv.called
    assert mock_socket.recv.call_args == call(SENSOR_TEST_CONFIG["buffer_size"])