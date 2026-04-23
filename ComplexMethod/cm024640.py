async def test_light_async_turn_on(hass: HomeAssistant) -> None:
    """Test turning the light on."""
    client = create_mock_client()
    client.priorities = [{const.KEY_PRIORITY: TEST_PRIORITY}]
    await setup_test_config_entry(hass, hyperion_client=client)

    # On (=), 100% (=), solid (=), [255,255,255] (=)
    client.async_send_set_color = AsyncMock(return_value=True)
    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: TEST_ENTITY_ID_1}, blocking=True
    )

    assert client.async_send_set_color.call_args == call(
        **{
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_COLOR: [255, 255, 255],
            const.KEY_ORIGIN: DEFAULT_ORIGIN,
        }
    )

    # On (=), 50% (!), solid (=), [255,255,255] (=)
    # ===
    brightness = 128
    client.async_send_set_color = AsyncMock(return_value=True)
    client.async_send_set_adjustment = AsyncMock(return_value=True)
    client.adjustment = [{const.KEY_ID: TEST_ID}]
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID_1, ATTR_BRIGHTNESS: brightness},
        blocking=True,
    )

    assert client.async_send_set_adjustment.call_args == call(
        **{const.KEY_ADJUSTMENT: {const.KEY_BRIGHTNESS: 50, const.KEY_ID: TEST_ID}}
    )
    assert client.async_send_set_color.call_args == call(
        **{
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_COLOR: [255, 255, 255],
            const.KEY_ORIGIN: DEFAULT_ORIGIN,
        }
    )

    # Simulate a false return of async_send_set_adjustment
    client.async_send_set_adjustment = AsyncMock(return_value=False)
    client.adjustment = [{const.KEY_ID: TEST_ID}]
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID_1, ATTR_BRIGHTNESS: brightness},
        blocking=True,
    )

    # Simulate a state callback from Hyperion.
    client.adjustment = [{const.KEY_BRIGHTNESS: 50}]
    call_registered_callback(client, "adjustment-update")
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.state == "on"
    assert entity_state.attributes["brightness"] == brightness

    # On (=), 50% (=), solid (=), [0,255,255] (!)
    hs_color = (180.0, 100.0)
    client.async_send_set_color = AsyncMock(return_value=True)
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID_1, ATTR_HS_COLOR: hs_color},
        blocking=True,
    )

    assert client.async_send_set_color.call_args == call(
        **{
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_COLOR: (0, 255, 255),
            const.KEY_ORIGIN: DEFAULT_ORIGIN,
        }
    )

    # Simulate a state callback from Hyperion.
    client.priorities = [
        {
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_COMPONENTID: const.KEY_COMPONENTID_COLOR,
            const.KEY_VALUE: {const.KEY_RGB: (0, 255, 255)},
            const.KEY_OWNER: "System",
        }
    ]

    call_registered_callback(client, "priorities-update")
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.attributes["hs_color"] == hs_color
    assert entity_state.attributes["icon"] == hyperion_light.ICON_LIGHTBULB

    # On (=), 100% (!), solid, [0,255,255] (=)
    brightness = 255
    client.async_send_set_color = AsyncMock(return_value=True)
    client.async_send_set_adjustment = AsyncMock(return_value=True)
    client.adjustment = [{const.KEY_ID: TEST_ID}]

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID_1, ATTR_BRIGHTNESS: brightness},
        blocking=True,
    )

    assert client.async_send_set_adjustment.call_args == call(
        **{const.KEY_ADJUSTMENT: {const.KEY_BRIGHTNESS: 100, const.KEY_ID: TEST_ID}}
    )
    assert client.async_send_set_color.call_args == call(
        **{
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_COLOR: (0, 255, 255),
            const.KEY_ORIGIN: DEFAULT_ORIGIN,
        }
    )
    client.adjustment = [{const.KEY_BRIGHTNESS: 100}]
    call_registered_callback(client, "adjustment-update")
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.attributes["brightness"] == brightness

    # On (=), 100% (=), "Warm Blobs" (!), [0,255,255] (=)
    effect = "Warm Blobs"
    client.async_send_clear = AsyncMock(return_value=True)
    client.async_send_set_effect = AsyncMock(return_value=True)

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID_1, ATTR_EFFECT: effect},
        blocking=True,
    )

    assert client.async_send_set_effect.call_args == call(
        **{
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_EFFECT: {const.KEY_NAME: effect},
            const.KEY_ORIGIN: DEFAULT_ORIGIN,
        }
    )
    client.priorities = [
        {
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_COMPONENTID: const.KEY_COMPONENTID_EFFECT,
            const.KEY_OWNER: effect,
        }
    ]
    call_registered_callback(client, "priorities-update")
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.attributes["icon"] == hyperion_light.ICON_EFFECT
    assert entity_state.attributes["effect"] == effect

    # On (=), 100% (=), [0,0,255] (!)
    # Ensure changing the color will move the effect to 'Solid' automatically.
    hs_color = (240.0, 100.0)
    client.async_send_set_color = AsyncMock(return_value=True)
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID_1, ATTR_HS_COLOR: hs_color},
        blocking=True,
    )

    assert client.async_send_set_color.call_args == call(
        **{
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_COLOR: (0, 0, 255),
            const.KEY_ORIGIN: DEFAULT_ORIGIN,
        }
    )
    # Simulate a state callback from Hyperion.
    client.priorities = [
        {
            const.KEY_PRIORITY: TEST_PRIORITY,
            const.KEY_COMPONENTID: const.KEY_COMPONENTID_COLOR,
            const.KEY_VALUE: {const.KEY_RGB: (0, 0, 255)},
            const.KEY_OWNER: "System",
        }
    ]
    call_registered_callback(client, "priorities-update")
    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.attributes["hs_color"] == hs_color
    assert entity_state.attributes["icon"] == hyperion_light.ICON_LIGHTBULB
    assert entity_state.attributes["effect"] == hyperion_light.KEY_EFFECT_SOLID

    # No calls if disconnected.
    client.has_loaded_state = False
    call_registered_callback(client, "client-update", {"loaded-state": False})
    client.async_send_clear = AsyncMock(return_value=True)
    client.async_send_set_effect = AsyncMock(return_value=True)

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: TEST_ENTITY_ID_1}, blocking=True
    )

    assert not client.async_send_clear.called
    assert not client.async_send_set_effect.called