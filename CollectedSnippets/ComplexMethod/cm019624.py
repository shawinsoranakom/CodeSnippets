async def test_cover_position_aware_lift(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
    entity_id: str,
) -> None:
    """Test window covering devices with position aware lift features."""

    state = hass.states.get(entity_id)
    assert state
    mask = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )
    assert state.attributes["supported_features"] & mask == mask

    for position in (0, 9999):
        set_node_attribute(matter_node, 1, 258, 14, position)
        set_node_attribute(matter_node, 1, 258, 10, 0b000000)
        await trigger_subscription_callback(hass, matter_client)

        state = hass.states.get(entity_id)
        assert state
        assert state.attributes["current_position"] == 100 - floor(position / 100)
        assert state.state == CoverState.OPEN

    set_node_attribute(matter_node, 1, 258, 14, 10000)
    set_node_attribute(matter_node, 1, 258, 10, 0b000000)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["current_position"] == 0
    assert state.state == CoverState.CLOSED