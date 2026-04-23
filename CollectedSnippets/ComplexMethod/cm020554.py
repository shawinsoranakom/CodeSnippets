async def test_cover_position(
    hass: HomeAssistant, setup_integration: None, mock_publish_state: AsyncMock
) -> None:
    """Test cover positions."""

    attributes = hass.states.get(_ENTITY_ID_POS).attributes
    assert attributes.get("supported_features") == (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
    )

    # Cover open
    mock_publish_state.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: _ENTITY_ID_POS},
        blocking=True,
    )

    publish_state = _get_publish_state(mock_publish_state)
    assert publish_state.read_position() == 100

    async_fire_mqtt_message(hass, _TOPIC_POS_STATE, _PAYLOAD_POS_STATE_OPENED)
    await hass.async_block_till_done()

    entity_state = hass.states.get(_ENTITY_ID_POS)
    assert entity_state.state == CoverState.OPEN
    assert entity_state.attributes[ATTR_CURRENT_POSITION] == 100

    # Cover position
    mock_publish_state.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: _ENTITY_ID_POS, ATTR_POSITION: 50},
        blocking=True,
    )

    publish_state = _get_publish_state(mock_publish_state)
    assert publish_state.read_position() == 50

    async_fire_mqtt_message(hass, _TOPIC_POS_STATE, _PAYLOAD_POS_STATE_POSITION)
    await hass.async_block_till_done()

    entity_state = hass.states.get(_ENTITY_ID_POS)
    assert entity_state.state == CoverState.OPEN
    assert entity_state.attributes[ATTR_CURRENT_POSITION] == 50

    # Cover close
    mock_publish_state.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: _ENTITY_ID_POS},
        blocking=True,
    )

    publish_state = _get_publish_state(mock_publish_state)
    assert publish_state.read_position() == 0

    async_fire_mqtt_message(hass, _TOPIC_POS_STATE, _PAYLOAD_POS_STATE_CLOSED)
    await hass.async_block_till_done()

    entity_state = hass.states.get(_ENTITY_ID_POS)
    assert entity_state.state == CoverState.CLOSED
    assert entity_state.attributes[ATTR_CURRENT_POSITION] == 0