async def test_generic_switch_multi_node(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test event entity for a GenericSwitch node with multiple buttons."""
    state_button_1 = hass.states.get("event.mock_generic_switch_button_1")
    assert state_button_1
    assert state_button_1.state == "unknown"
    # name should be 'DeviceName Button (1)'
    assert state_button_1.name == "Mock Generic Switch Button (1)"
    # check event_types from featuremap 30 (0b11110) and MultiPressMax unset (default 2)
    assert state_button_1.attributes[ATTR_EVENT_TYPES] == [
        "multi_press_1",
        "multi_press_2",
        "long_press",
        "long_release",
    ]
    # check button 2
    state_button_2 = hass.states.get("event.mock_generic_switch_button_fancy_button")
    assert state_button_2
    assert state_button_2.state == "unknown"
    # name should be 'DeviceName Button (Fancy Button)' due to ha_entitylabel 'Fancy Button'
    assert state_button_2.name == "Mock Generic Switch Button (Fancy Button)"
    # check event_types from featuremap 30 (0b11110) and MultiPressMax 4
    assert state_button_2.attributes[ATTR_EVENT_TYPES] == [
        "multi_press_1",
        "multi_press_2",
        "multi_press_3",
        "multi_press_4",
        "long_press",
        "long_release",
    ]

    # trigger firing a multi press event
    await trigger_subscription_callback(
        hass,
        matter_client,
        EventType.NODE_EVENT,
        MatterNodeEvent(
            node_id=matter_node.node_id,
            endpoint_id=1,
            cluster_id=59,
            event_id=6,
            event_number=0,
            priority=1,
            timestamp=0,
            timestamp_type=0,
            data={"totalNumberOfPressesCounted": 2},
        ),
    )
    state = hass.states.get("event.mock_generic_switch_button_1")
    assert state.attributes[ATTR_EVENT_TYPE] == "multi_press_2"