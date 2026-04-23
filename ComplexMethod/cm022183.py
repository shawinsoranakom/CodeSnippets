def test_aprs_listener_rx_msg(mock_ais: MagicMock) -> None:
    """Test rx_msg."""
    callsign = TEST_CALLSIGN
    password = TEST_PASSWORD
    host = TEST_HOST
    server_filter = TEST_FILTER
    see = Mock()

    sample_msg = {
        device_tracker.ATTR_FORMAT: "uncompressed",
        device_tracker.ATTR_FROM: "ZZ0FOOBAR-1",
        device_tracker.ATTR_LATITUDE: 0.0,
        device_tracker.ATTR_LONGITUDE: 0.0,
        device_tracker.ATTR_ALTITUDE: 0,
    }

    listener = device_tracker.AprsListenerThread(
        callsign, password, host, server_filter, see
    )
    listener.run()
    listener.rx_msg(sample_msg)

    assert listener.callsign == callsign
    assert listener.host == host
    assert listener.server_filter == server_filter
    assert listener.see == see
    assert listener.start_event.is_set()
    assert listener.start_success
    assert listener.start_message == "Connected to testhost with callsign testcall."
    see.assert_called_with(
        dev_id=device_tracker.slugify("ZZ0FOOBAR-1"),
        gps=(0.0, 0.0),
        attributes={"altitude": 0},
    )