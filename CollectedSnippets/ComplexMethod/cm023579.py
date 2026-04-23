async def test_report_with_string_state(
    hass: HomeAssistant, mock_socket, mock_time
) -> None:
    """Test the reporting with strings."""
    expected = [
        "ha.test.entity.foo 1.000000 12345",
        "ha.test.entity.state 1.000000 12345",
    ]

    mock_time.return_value = 12345
    assert await async_setup_component(hass, graphite.DOMAIN, {"graphite": {}})
    await hass.async_block_till_done()
    mock_socket.reset_mock()

    await hass.async_start()
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "above_horizon", {"foo": 1.0})
    await hass.async_block_till_done()
    hass.data[graphite.DOMAIN]._queue.join()

    assert mock_socket.return_value.connect.call_count == 1
    assert mock_socket.return_value.connect.call_args == mock.call(("localhost", 2003))
    assert mock_socket.return_value.sendall.call_count == 1
    assert mock_socket.return_value.sendall.call_args == mock.call(
        "\n".join(expected).encode("utf-8")
    )
    assert mock_socket.return_value.send.call_count == 1
    assert mock_socket.return_value.send.call_args == mock.call(b"\n")
    assert mock_socket.return_value.close.call_count == 1

    mock_socket.reset_mock()

    hass.states.async_set("test.entity", "not_float")
    await hass.async_block_till_done()
    hass.data[graphite.DOMAIN]._queue.join()

    assert mock_socket.return_value.connect.call_count == 0
    assert mock_socket.return_value.sendall.call_count == 0
    assert mock_socket.return_value.send.call_count == 0
    assert mock_socket.return_value.close.call_count == 0