async def test_client_state_update(
    hass: HomeAssistant,
    mock_websocket_message: WebsocketMessageMock,
    config_entry_factory: ConfigEntryFactoryType,
    client_payload: list[dict[str, Any]],
) -> None:
    """Verify tracking of wireless clients."""
    # A normal client with current timestamp should have STATE_HOME, this is wired bug
    client_payload[1] |= {"last_seen": dt_util.as_timestamp(dt_util.utcnow())}
    await config_entry_factory()

    assert len(hass.states.async_entity_ids(TRACKER_DOMAIN)) == 3

    assert hass.states.get("device_tracker.ws_client_1").state == STATE_NOT_HOME
    assert (
        hass.states.get("device_tracker.ws_client_1").attributes["host_name"]
        == "ws_client_1"
    )

    # Wireless client with wired bug, if bug active on restart mark device away
    assert hass.states.get("device_tracker.wd_bug_client").state == STATE_NOT_HOME

    # A client that has never been seen should be marked away.
    assert hass.states.get("device_tracker.unseen_client").state == STATE_NOT_HOME

    # Updated timestamp marks client as home
    ws_client_1 = client_payload[0] | {
        "last_seen": dt_util.as_timestamp(dt_util.utcnow())
    }
    mock_websocket_message(message=MessageKey.CLIENT, data=ws_client_1)
    await hass.async_block_till_done()

    assert hass.states.get("device_tracker.ws_client_1").state == STATE_HOME

    # Change time to mark client as away
    new_time = dt_util.utcnow() + timedelta(seconds=DEFAULT_DETECTION_TIME)
    with freeze_time(new_time):
        async_fire_time_changed(hass, new_time)
        await hass.async_block_till_done()

    assert hass.states.get("device_tracker.ws_client_1").state == STATE_NOT_HOME

    # Same timestamp doesn't explicitly mark client as away
    mock_websocket_message(message=MessageKey.CLIENT, data=ws_client_1)
    await hass.async_block_till_done()

    assert hass.states.get("device_tracker.ws_client_1").state == STATE_HOME