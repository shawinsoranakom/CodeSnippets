async def test_cover_full_features(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test window covering devices with all the features."""
    entity_id = "cover.mock_full_window_covering"

    state = hass.states.get(entity_id)
    assert state
    mask = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.SET_TILT_POSITION
    )
    assert state.attributes["supported_features"] & mask == mask

    set_node_attribute(matter_node, 1, 258, 14, 10000)
    set_node_attribute(matter_node, 1, 258, 15, 10000)
    set_node_attribute(matter_node, 1, 258, 10, 0b000000)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == CoverState.CLOSED

    set_node_attribute(matter_node, 1, 258, 14, 5000)
    set_node_attribute(matter_node, 1, 258, 15, 10000)
    set_node_attribute(matter_node, 1, 258, 10, 0b000000)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == CoverState.OPEN

    set_node_attribute(matter_node, 1, 258, 14, 10000)
    set_node_attribute(matter_node, 1, 258, 15, 5000)
    set_node_attribute(matter_node, 1, 258, 10, 0b000000)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == CoverState.CLOSED

    set_node_attribute(matter_node, 1, 258, 14, 5000)
    set_node_attribute(matter_node, 1, 258, 15, 5000)
    set_node_attribute(matter_node, 1, 258, 10, 0b000000)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == CoverState.OPEN

    set_node_attribute(matter_node, 1, 258, 14, 5000)
    set_node_attribute(matter_node, 1, 258, 15, None)
    set_node_attribute(matter_node, 1, 258, 10, 0b000000)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == CoverState.OPEN

    set_node_attribute(matter_node, 1, 258, 14, None)
    set_node_attribute(matter_node, 1, 258, 15, 5000)
    set_node_attribute(matter_node, 1, 258, 10, 0b000000)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "unknown"

    set_node_attribute(matter_node, 1, 258, 14, 10000)
    set_node_attribute(matter_node, 1, 258, 15, None)
    set_node_attribute(matter_node, 1, 258, 10, 0b000000)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == CoverState.CLOSED

    set_node_attribute(matter_node, 1, 258, 14, None)
    set_node_attribute(matter_node, 1, 258, 15, 10000)
    set_node_attribute(matter_node, 1, 258, 10, 0b000000)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "unknown"

    set_node_attribute(matter_node, 1, 258, 14, None)
    set_node_attribute(matter_node, 1, 258, 15, None)
    set_node_attribute(matter_node, 1, 258, 10, 0b000000)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "unknown"