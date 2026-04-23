async def test_cover_up_down_stop(
    hass: HomeAssistant, setup_integration: None, mock_publish_state: AsyncMock
) -> None:
    """Test cover up, down and stop."""

    attributes = hass.states.get(_ENTITY_ID_UDS).attributes
    assert attributes.get("supported_features") == (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    # Cover open
    mock_publish_state.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: _ENTITY_ID_UDS},
        blocking=True,
    )

    publish_state = _get_publish_state(mock_publish_state)
    assert publish_state.read_state() == "up"

    # Simulate response
    async_fire_mqtt_message(hass, _TOPIC_UDS_STATE, _PAYLOAD_UDS_STATE_OPENED)
    await hass.async_block_till_done()

    assert hass.states.get(_ENTITY_ID_UDS).state == CoverState.OPEN

    # Cover close
    mock_publish_state.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: _ENTITY_ID_UDS},
        blocking=True,
    )

    publish_state = _get_publish_state(mock_publish_state)
    assert publish_state.read_state() == "down"

    # Simulate response
    async_fire_mqtt_message(hass, _TOPIC_UDS_STATE, _PAYLOAD_UDS_STATE_CLOSED)
    await hass.async_block_till_done()

    assert hass.states.get(_ENTITY_ID_UDS).state == CoverState.OPEN

    # Cover stop
    mock_publish_state.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: _ENTITY_ID_UDS},
        blocking=True,
    )

    publish_state = _get_publish_state(mock_publish_state)
    assert publish_state.read_state() == "stop"

    # Simulate response
    async_fire_mqtt_message(hass, _TOPIC_UDS_STATE, _PAYLOAD_UDS_STATE_STOPPED)
    await hass.async_block_till_done()

    assert hass.states.get(_ENTITY_ID_UDS).state == CoverState.CLOSED