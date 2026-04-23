async def test_tvoc_level_sensor(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test TVOC level sensor (LevelIndication feature)."""
    # TVOC Level - initial state is low (attribute 10 = 1 in fixture)
    state = hass.states.get("sensor.mock_air_purifier_tvoc_level")
    assert state
    assert state.state == "low"
    assert state.attributes["device_class"] == "enum"
    assert state.attributes["options"] == ["low", "medium", "high", "critical"]

    # Test changing to medium level (2)
    set_node_attribute(matter_node, 2, 1070, 10, 2)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.mock_air_purifier_tvoc_level")
    assert state
    assert state.state == "medium"

    # Test changing to high level (3)
    set_node_attribute(matter_node, 2, 1070, 10, 3)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.mock_air_purifier_tvoc_level")
    assert state
    assert state.state == "high"

    # Test changing to critical level (4)
    set_node_attribute(matter_node, 2, 1070, 10, 4)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.mock_air_purifier_tvoc_level")
    assert state
    assert state.state == "critical"

    # Test changing to unknown level (0)
    set_node_attribute(matter_node, 2, 1070, 10, 0)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.mock_air_purifier_tvoc_level")
    assert state
    assert state.state == "unknown"