def test_aprs_listener_stop(mock_ais: MagicMock) -> None:
    """Test listener thread stop."""
    callsign = TEST_CALLSIGN
    password = TEST_PASSWORD
    host = TEST_HOST
    server_filter = TEST_FILTER
    see = Mock()

    listener = device_tracker.AprsListenerThread(
        callsign, password, host, server_filter, see
    )
    listener.ais.close = Mock()
    listener.run()
    listener.stop()

    assert listener.callsign == callsign
    assert listener.host == host
    assert listener.server_filter == server_filter
    assert listener.see == see
    assert listener.start_event.is_set()
    assert listener.start_message == "Connected to testhost with callsign testcall."
    assert listener.start_success
    listener.ais.close.assert_called_with()