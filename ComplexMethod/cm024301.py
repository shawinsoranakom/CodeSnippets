async def test_current_cover_position_inverted(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the current cover position."""
    await mqtt_mock_entry()

    state_attributes_dict = hass.states.get("cover.test").attributes
    assert ATTR_CURRENT_POSITION not in state_attributes_dict
    assert ATTR_CURRENT_TILT_POSITION not in state_attributes_dict
    assert 4 & hass.states.get("cover.test").attributes["supported_features"] != 4

    async_fire_mqtt_message(hass, "get-position-topic", "100")
    current_percentage_cover_position = hass.states.get("cover.test").attributes[
        ATTR_CURRENT_POSITION
    ]
    assert current_percentage_cover_position == 0
    assert hass.states.get("cover.test").state == CoverState.CLOSED

    async_fire_mqtt_message(hass, "get-position-topic", "0")
    current_percentage_cover_position = hass.states.get("cover.test").attributes[
        ATTR_CURRENT_POSITION
    ]
    assert current_percentage_cover_position == 100
    assert hass.states.get("cover.test").state == CoverState.OPEN

    async_fire_mqtt_message(hass, "get-position-topic", "50")
    current_percentage_cover_position = hass.states.get("cover.test").attributes[
        ATTR_CURRENT_POSITION
    ]
    assert current_percentage_cover_position == 50
    assert hass.states.get("cover.test").state == CoverState.OPEN

    async_fire_mqtt_message(hass, "get-position-topic", "non-numeric")
    current_percentage_cover_position = hass.states.get("cover.test").attributes[
        ATTR_CURRENT_POSITION
    ]
    assert current_percentage_cover_position == 50
    assert hass.states.get("cover.test").state == CoverState.OPEN

    async_fire_mqtt_message(hass, "get-position-topic", "101")
    current_percentage_cover_position = hass.states.get("cover.test").attributes[
        ATTR_CURRENT_POSITION
    ]
    assert current_percentage_cover_position == 0
    assert hass.states.get("cover.test").state == CoverState.CLOSED