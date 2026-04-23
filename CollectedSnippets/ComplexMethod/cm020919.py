async def test_hub_state_change(
    hass: HomeAssistant,
    mock_websocket_state: WebsocketStateManager,
) -> None:
    """Verify entities state reflect on hub connection becoming unavailable."""
    assert len(hass.states.async_entity_ids(TRACKER_DOMAIN)) == 2
    assert hass.states.get("device_tracker.ws_client_1").state == STATE_NOT_HOME
    assert hass.states.get("device_tracker.switch_1").state == STATE_HOME

    # Controller unavailable
    await mock_websocket_state.disconnect()
    assert hass.states.get("device_tracker.ws_client_1").state == STATE_UNAVAILABLE
    assert hass.states.get("device_tracker.switch_1").state == STATE_UNAVAILABLE

    # Controller available
    await mock_websocket_state.reconnect()
    assert hass.states.get("device_tracker.ws_client_1").state == STATE_NOT_HOME
    assert hass.states.get("device_tracker.switch_1").state == STATE_HOME