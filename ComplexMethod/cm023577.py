async def test_shutdown(hass: HomeAssistant, mock_socket, mock_time) -> None:
    """Test the shutdown."""
    mock_time.return_value = 12345
    assert await async_setup_component(hass, graphite.DOMAIN, {"graphite": {}})
    await hass.async_block_till_done()
    mock_socket.reset_mock()

    await hass.async_start()
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", STATE_ON)
    await hass.async_block_till_done()
    hass.data[graphite.DOMAIN]._queue.join()

    assert mock_socket.return_value.connect.call_count == 1
    assert mock_socket.return_value.connect.call_args == mock.call(("localhost", 2003))
    assert mock_socket.return_value.sendall.call_count == 1
    assert mock_socket.return_value.sendall.call_args == mock.call(
        b"ha.test.entity.state 1.000000 12345"
    )
    assert mock_socket.return_value.send.call_count == 1
    assert mock_socket.return_value.send.call_args == mock.call(b"\n")
    assert mock_socket.return_value.close.call_count == 1

    mock_socket.reset_mock()

    await hass.async_stop()
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", STATE_OFF)
    await hass.async_block_till_done()

    assert mock_socket.return_value.connect.call_count == 0
    assert mock_socket.return_value.sendall.call_count == 0