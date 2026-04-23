def test_aprs_listener(mock_ais: MagicMock) -> None:
    """Test listener thread."""
    callsign = TEST_CALLSIGN
    password = TEST_PASSWORD
    host = TEST_HOST
    server_filter = TEST_FILTER
    port = DEFAULT_PORT
    see = Mock()

    listener = device_tracker.AprsListenerThread(
        callsign, password, host, server_filter, see
    )
    listener.run()

    assert listener.callsign == callsign
    assert listener.host == host
    assert listener.server_filter == server_filter
    assert listener.see == see
    assert listener.start_event.is_set()
    assert listener.start_success
    assert listener.start_message == "Connected to testhost with callsign testcall."
    mock_ais.assert_called_with(callsign, passwd=password, host=host, port=port)