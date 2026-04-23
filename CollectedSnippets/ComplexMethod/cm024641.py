async def test_light_async_updates_from_hyperion_client(
    hass: HomeAssistant,
) -> None:
    """Test receiving a variety of Hyperion client callbacks."""
    client = create_mock_client()
    client.priorities = [{const.KEY_PRIORITY: TEST_PRIORITY}]
    await setup_test_config_entry(hass, hyperion_client=client)

    # Bright change gets accepted.
    brightness = 10
    client.adjustment = [{const.KEY_BRIGHTNESS: brightness}]
    call_registered_callback(client, "adjustment-update")
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.state == "on"
    assert entity_state.attributes["brightness"] == round(255 * (brightness / 100.0))

    # Broken brightness value is ignored.
    bad_brightness = -200
    client.adjustment = [{const.KEY_BRIGHTNESS: bad_brightness}]
    call_registered_callback(client, "adjustment-update")
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.state == "on"
    assert entity_state.attributes["brightness"] == round(255 * (brightness / 100.0))

    # Update priorities (Effect)
    effect = "foo"
    client.priorities = [
        {
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_COMPONENTID: const.KEY_COMPONENTID_EFFECT,
            const.KEY_OWNER: effect,
            const.KEY_VISIBLE: True,
            const.KEY_ORIGIN: "System",
        }
    ]

    call_registered_callback(client, "priorities-update")
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.attributes["effect"] == effect
    assert entity_state.attributes["icon"] == hyperion_light.ICON_EFFECT
    assert entity_state.attributes["hs_color"] == (0.0, 0.0)

    # Update priorities (Color)
    rgb = (0, 100, 100)
    client.priorities = [
        {
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_COMPONENTID: const.KEY_COMPONENTID_COLOR,
            const.KEY_VALUE: {const.KEY_RGB: rgb},
            const.KEY_VISIBLE: True,
            const.KEY_ORIGIN: "System",
            const.KEY_OWNER: "System",
        }
    ]

    call_registered_callback(client, "priorities-update")
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.attributes["effect"] == hyperion_light.KEY_EFFECT_SOLID
    assert entity_state.attributes["icon"] == hyperion_light.ICON_LIGHTBULB
    assert entity_state.attributes["hs_color"] == (180.0, 100.0)

    # Update priorities (None)
    client.priorities = []

    call_registered_callback(client, "priorities-update")
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.state == "off"

    # Update effect list
    effects = [{const.KEY_NAME: "One"}, {const.KEY_NAME: "Two"}]
    client.effects = effects
    call_registered_callback(client, "effects-update")
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.attributes["effect_list"] == [
        hyperion_light.KEY_EFFECT_SOLID
    ] + [effect[const.KEY_NAME] for effect in effects]

    # Update connection status (e.g. disconnection).

    # Turn on late, check state, disconnect, ensure it cannot be turned off.
    client.has_loaded_state = False
    call_registered_callback(client, "client-update", {"loaded-state": False})
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.state == "unavailable"

    # Update connection status (e.g. re-connection)
    client.has_loaded_state = True
    client.priorities = [
        {
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_COMPONENTID: const.KEY_COMPONENTID_COLOR,
            const.KEY_VALUE: {const.KEY_RGB: rgb},
            const.KEY_VISIBLE: True,
            const.KEY_ORIGIN: "System",
            const.KEY_OWNER: "System",
        }
    ]
    call_registered_callback(client, "client-update", {"loaded-state": True})
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.state == "on"