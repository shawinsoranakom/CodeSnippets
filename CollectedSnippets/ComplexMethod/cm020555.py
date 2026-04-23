async def test_cover_slats(
    hass: HomeAssistant, setup_integration: None, mock_publish_state: AsyncMock
) -> None:
    """Test cover slats."""

    attributes = hass.states.get(_ENTITY_ID_SLAT).attributes
    assert attributes.get("supported_features") == (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.OPEN_TILT
        | CoverEntityFeature.CLOSE_TILT
        | CoverEntityFeature.SET_TILT_POSITION
    )

    # Start with a fully closed cover
    mock_publish_state.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: _ENTITY_ID_SLAT},
        blocking=True,
    )

    publish_state = _get_publish_state(mock_publish_state)
    assert publish_state.read_position() == 0
    assert publish_state.read_slat_position() == 0

    async_fire_mqtt_message(hass, _TOPIC_SLAT_STATE, _PAYLOAD_SLAT_STATE_FULLY_CLOSED)
    await hass.async_block_till_done()

    entity_state = hass.states.get(_ENTITY_ID_SLAT)
    assert entity_state.state == CoverState.CLOSED
    assert entity_state.attributes[ATTR_CURRENT_POSITION] == 0
    assert entity_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    # Slat open
    mock_publish_state.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: _ENTITY_ID_SLAT},
        blocking=True,
    )

    publish_state = _get_publish_state(mock_publish_state)
    assert publish_state.read_slat_position() == 50

    async_fire_mqtt_message(hass, _TOPIC_SLAT_STATE, _PAYLOAD_SLAT_STATE_OPENED)
    await hass.async_block_till_done()

    entity_state = hass.states.get(_ENTITY_ID_SLAT)
    assert entity_state.state == CoverState.OPEN
    assert entity_state.attributes[ATTR_CURRENT_TILT_POSITION] == 50

    # SLat position
    mock_publish_state.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: _ENTITY_ID_SLAT, ATTR_TILT_POSITION: 75},
        blocking=True,
    )

    publish_state = _get_publish_state(mock_publish_state)
    assert publish_state.read_slat_position() == 75

    async_fire_mqtt_message(hass, _TOPIC_SLAT_STATE, _PAYLOAD_SLAT_STATE_POSITION)
    await hass.async_block_till_done()

    entity_state = hass.states.get(_ENTITY_ID_SLAT)
    assert entity_state.state == CoverState.OPEN
    assert entity_state.attributes[ATTR_CURRENT_TILT_POSITION] == 75

    # Slat close
    mock_publish_state.reset_mock()
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: _ENTITY_ID_SLAT},
        blocking=True,
    )

    publish_state = _get_publish_state(mock_publish_state)
    assert publish_state.read_slat_position() == 0

    async_fire_mqtt_message(hass, _TOPIC_SLAT_STATE, _PAYLOAD_SLAT_STATE_CLOSED)
    await hass.async_block_till_done()

    entity_state = hass.states.get(_ENTITY_ID_SLAT)
    assert entity_state.state == CoverState.CLOSED
    assert entity_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0