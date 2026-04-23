async def test_lock_attributes(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test door lock attributes."""
    # WrongCodeEntryLimit for door lock
    state = hass.states.get("number.mock_door_lock_wrong_code_limit")
    assert state
    assert state.state == "3"

    set_node_attribute(matter_node, 1, 257, 48, 10)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("number.mock_door_lock_wrong_code_limit")
    assert state
    assert state.state == "10"

    # UserCodeTemporaryDisableTime for door lock
    state = hass.states.get("number.mock_door_lock_user_code_temporary_disable_time")
    assert state
    assert state.state == "10"

    set_node_attribute(matter_node, 1, 257, 49, 30)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("number.mock_door_lock_user_code_temporary_disable_time")
    assert state
    assert state.state == "30"