async def test_ssl_state(
    hass: HomeAssistant, mock_socket, mock_select, mock_ssl_context
) -> None:
    """Return the contents of _state, updated over SSL."""
    config = copy(SENSOR_TEST_CONFIG)
    config[tcp.CONF_SSL] = "on"

    assert await async_setup_component(hass, "sensor", {"sensor": config})
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY)

    assert state
    assert state.state == "7.123567"
    assert mock_socket.connect.called
    assert mock_socket.connect.call_args == call(
        (SENSOR_TEST_CONFIG["host"], SENSOR_TEST_CONFIG["port"])
    )
    assert not mock_socket.send.called
    assert mock_ssl_context.called
    assert mock_ssl_context.return_value.check_hostname
    mock_ssl_socket = mock_ssl_context.return_value.wrap_socket.return_value
    assert mock_ssl_socket.send.called
    assert mock_ssl_socket.send.call_args == call(
        SENSOR_TEST_CONFIG["payload"].encode()
    )
    assert mock_select.call_args == call(
        [mock_ssl_socket], [], [], SENSOR_TEST_CONFIG[tcp.CONF_TIMEOUT]
    )
    assert mock_ssl_socket.recv.called
    assert mock_ssl_socket.recv.call_args == call(SENSOR_TEST_CONFIG["buffer_size"])