async def test_lock_popp_electric_strike_lock_control_select(
    hass: HomeAssistant, client, lock_popp_electric_strike_lock_control, integration
) -> None:
    """Test that the Popp Electric Strike Lock Control select entity."""
    LOCK_SELECT_ENTITY = "select.node_62_current_lock_mode"
    state = hass.states.get(LOCK_SELECT_ENTITY)
    assert state
    assert state.state == "Unsecured"
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": LOCK_SELECT_ENTITY, "option": "UnsecuredWithTimeout"},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == lock_popp_electric_strike_lock_control.node_id
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 98,
        "property": "targetMode",
    }
    assert args["value"] == 1