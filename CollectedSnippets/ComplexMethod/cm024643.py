async def test_switch_turn_on_off(hass: HomeAssistant) -> None:
    """Test turning the light on."""
    client = create_mock_client()
    client.async_send_set_component = AsyncMock(return_value=True)
    client.components = TEST_COMPONENTS

    # Setup component switch.
    register_test_entity(
        hass,
        SWITCH_DOMAIN,
        f"{TYPE_HYPERION_COMPONENT_SWITCH_BASE}_all",
        TEST_SWITCH_COMPONENT_ALL_ENTITY_ID,
    )
    await setup_test_config_entry(hass, hyperion_client=client)

    # Verify switch is on (as per TEST_COMPONENTS above).
    entity_state = hass.states.get(TEST_SWITCH_COMPONENT_ALL_ENTITY_ID)
    assert entity_state
    assert entity_state.state == "on"

    # Turn switch off.
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: TEST_SWITCH_COMPONENT_ALL_ENTITY_ID},
        blocking=True,
    )

    # Verify correct parameters are passed to the library.
    assert client.async_send_set_component.call_args == call(
        **{KEY_COMPONENTSTATE: {KEY_COMPONENT: KEY_COMPONENTID_ALL, KEY_STATE: False}}
    )

    client.components[0] = {
        "enabled": False,
        "name": "ALL",
    }
    call_registered_callback(client, "components-update")

    # Verify the switch turns off.
    entity_state = hass.states.get(TEST_SWITCH_COMPONENT_ALL_ENTITY_ID)
    assert entity_state
    assert entity_state.state == "off"

    # Turn switch on.
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_SWITCH_COMPONENT_ALL_ENTITY_ID},
        blocking=True,
    )

    # Verify correct parameters are passed to the library.
    assert client.async_send_set_component.call_args == call(
        **{KEY_COMPONENTSTATE: {KEY_COMPONENT: KEY_COMPONENTID_ALL, KEY_STATE: True}}
    )

    client.components[0] = {
        "enabled": True,
        "name": "ALL",
    }
    call_registered_callback(client, "components-update")

    # Verify the switch turns on.
    entity_state = hass.states.get(TEST_SWITCH_COMPONENT_ALL_ENTITY_ID)
    assert entity_state
    assert entity_state.state == "on"