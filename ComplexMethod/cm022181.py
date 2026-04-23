def test_aprs_listener_start_fail() -> None:
    """Test listener thread start failure."""
    with patch.object(
        IS, "connect", side_effect=aprslib.ConnectionError("Unable to connect.")
    ):
        callsign = TEST_CALLSIGN
        password = TEST_PASSWORD
        host = TEST_HOST
        server_filter = TEST_FILTER
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
        assert not listener.start_success
        assert listener.start_message == "Unable to connect."