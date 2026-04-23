async def test_fan_base(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test Fan platform."""
    entity_id = "fan.mock_air_purifier"
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["preset_modes"] == [
        "low",
        "medium",
        "high",
        "auto",
        "natural_wind",
        "sleep_wind",
    ]
    assert state.attributes["direction"] == "forward"
    assert state.attributes["oscillating"] is False
    assert state.attributes["percentage"] is None
    assert state.attributes["percentage_step"] == 10
    assert state.attributes["preset_mode"] == "auto"
    mask = (
        FanEntityFeature.DIRECTION
        | FanEntityFeature.OSCILLATE
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.SET_SPEED
    )
    assert state.attributes["supported_features"] & mask == mask
    # handle fan mode update
    set_node_attribute(matter_node, 1, 514, 0, 1)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state.attributes["preset_mode"] == "low"
    # handle direction update
    set_node_attribute(matter_node, 1, 514, 11, 1)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state.attributes["direction"] == "reverse"
    # handle rock/oscillation update
    set_node_attribute(matter_node, 1, 514, 8, 1)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state.attributes["oscillating"] is True
    # handle wind mode active translates to correct preset
    set_node_attribute(matter_node, 1, 514, 10, 2)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state.attributes["preset_mode"] == "natural_wind"
    set_node_attribute(matter_node, 1, 514, 10, 1)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state.attributes["preset_mode"] == "sleep_wind"
    # set mains power to OFF (OnOff cluster)
    set_node_attribute(matter_node, 1, 6, 0, False)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state.attributes["preset_mode"] is None
    assert state.attributes["percentage"] == 0
    # test featuremap update
    set_node_attribute(matter_node, 1, 514, 65532, 1)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state.attributes["supported_features"] & FanEntityFeature.SET_SPEED