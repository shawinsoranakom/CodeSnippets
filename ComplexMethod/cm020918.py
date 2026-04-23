async def test_client_state_from_event_source(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_websocket_message: WebsocketMessageMock,
    client_payload: list[dict[str, Any]],
) -> None:
    """Verify update state of client based on event source."""

    async def mock_event(client: dict[str, Any], event_key: EventKey) -> dict[str, Any]:
        """Create and send event based on client payload."""
        event = {
            "user": client["mac"],
            "ssid": client["essid"],
            "hostname": client["hostname"],
            "ap": client["ap_mac"],
            "duration": 467,
            "bytes": 459039,
            "key": event_key,
            "subsystem": "wlan",
            "site_id": "name",
            "time": 1587752927000,
            "datetime": "2020-04-24T18:28:47Z",
            "_id": "5ea32ff730c49e00f90dca1a",
        }
        mock_websocket_message(message=MessageKey.EVENT, data=event)
        await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids(TRACKER_DOMAIN)) == 1
    assert hass.states.get("device_tracker.ws_client_1").state == STATE_NOT_HOME

    # State change signalling works with events

    # Connected event
    await mock_event(client_payload[0], EventKey.WIRELESS_CLIENT_CONNECTED)
    assert hass.states.get("device_tracker.ws_client_1").state == STATE_HOME

    # Disconnected event
    await mock_event(client_payload[0], EventKey.WIRELESS_CLIENT_DISCONNECTED)
    assert hass.states.get("device_tracker.ws_client_1").state == STATE_HOME

    # Change time to mark client as away
    freezer.tick(timedelta(seconds=(DEFAULT_DETECTION_TIME + 1)))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get("device_tracker.ws_client_1").state == STATE_NOT_HOME

    # To limit false positives in client tracker
    # data sources are prioritized when available
    # once real data is received events will be ignored.

    # New data
    ws_client_1 = client_payload[0] | {
        "last_seen": dt_util.as_timestamp(dt_util.utcnow())
    }
    mock_websocket_message(message=MessageKey.CLIENT, data=ws_client_1)
    await hass.async_block_till_done()
    assert hass.states.get("device_tracker.ws_client_1").state == STATE_HOME

    # Disconnection event will be ignored
    await mock_event(client_payload[0], EventKey.WIRELESS_CLIENT_DISCONNECTED)
    assert hass.states.get("device_tracker.ws_client_1").state == STATE_HOME

    # Change time to mark client as away
    freezer.tick(timedelta(seconds=(DEFAULT_DETECTION_TIME + 1)))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get("device_tracker.ws_client_1").state == STATE_NOT_HOME