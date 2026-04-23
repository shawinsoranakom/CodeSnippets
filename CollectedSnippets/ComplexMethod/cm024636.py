async def test_visible_effect_state_changes(hass: HomeAssistant) -> None:
    """Verify that state changes are processed as expected for visible effect sensor."""
    client = create_mock_client()
    client.components = TEST_COMPONENTS
    await setup_test_config_entry(hass, hyperion_client=client)

    # Simulate a platform grabber effect state callback from Hyperion.
    client.priorities = [
        {
            KEY_ACTIVE: True,
            KEY_COMPONENTID: "GRABBER",
            KEY_ORIGIN: "System",
            KEY_OWNER: "X11",
            KEY_PRIORITY: 250,
            KEY_VISIBLE: True,
        }
    ]

    call_registered_callback(client, "priorities-update")
    entity_state = hass.states.get(TEST_VISIBLE_EFFECT_SENSOR_ID)
    assert entity_state
    assert entity_state.state == client.priorities[0][KEY_OWNER]
    assert (
        entity_state.attributes["component_id"] == client.priorities[0][KEY_COMPONENTID]
    )
    assert entity_state.attributes["origin"] == client.priorities[0][KEY_ORIGIN]
    assert entity_state.attributes["priority"] == client.priorities[0][KEY_PRIORITY]

    # Simulate an effect state callback from Hyperion.
    client.priorities = [
        {
            KEY_ACTIVE: True,
            KEY_COMPONENTID: "EFFECT",
            KEY_ORIGIN: "System",
            KEY_OWNER: "Warm mood blobs",
            KEY_PRIORITY: 250,
            KEY_VISIBLE: True,
        }
    ]

    call_registered_callback(client, "priorities-update")
    entity_state = hass.states.get(TEST_VISIBLE_EFFECT_SENSOR_ID)
    assert entity_state
    assert entity_state.state == client.priorities[0][KEY_OWNER]
    assert (
        entity_state.attributes["component_id"] == client.priorities[0][KEY_COMPONENTID]
    )
    assert entity_state.attributes["origin"] == client.priorities[0][KEY_ORIGIN]
    assert entity_state.attributes["priority"] == client.priorities[0][KEY_PRIORITY]

    # Simulate a USB Capture state callback from Hyperion.
    client.priorities = [
        {
            KEY_ACTIVE: True,
            KEY_COMPONENTID: "V4L",
            KEY_ORIGIN: "System",
            KEY_OWNER: "V4L2",
            KEY_PRIORITY: 250,
            KEY_VISIBLE: True,
        }
    ]

    call_registered_callback(client, "priorities-update")
    entity_state = hass.states.get(TEST_VISIBLE_EFFECT_SENSOR_ID)
    assert entity_state
    assert entity_state.state == client.priorities[0][KEY_OWNER]
    assert (
        entity_state.attributes["component_id"] == client.priorities[0][KEY_COMPONENTID]
    )
    assert entity_state.attributes["origin"] == client.priorities[0][KEY_ORIGIN]
    assert entity_state.attributes["priority"] == client.priorities[0][KEY_PRIORITY]

    # Simulate a color effect state callback from Hyperion.
    client.priorities = [
        {
            KEY_ACTIVE: True,
            KEY_COMPONENTID: "COLOR",
            KEY_ORIGIN: "System",
            KEY_PRIORITY: 250,
            KEY_VALUE: {KEY_RGB: [0, 0, 0]},
            KEY_VISIBLE: True,
        }
    ]

    call_registered_callback(client, "priorities-update")
    entity_state = hass.states.get(TEST_VISIBLE_EFFECT_SENSOR_ID)
    assert entity_state
    assert entity_state.state == str(client.priorities[0][KEY_VALUE][KEY_RGB])
    assert (
        entity_state.attributes["component_id"] == client.priorities[0][KEY_COMPONENTID]
    )
    assert entity_state.attributes["origin"] == client.priorities[0][KEY_ORIGIN]
    assert entity_state.attributes["priority"] == client.priorities[0][KEY_PRIORITY]
    assert entity_state.attributes["color"] == client.priorities[0][KEY_VALUE]