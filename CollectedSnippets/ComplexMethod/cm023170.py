async def test_opening_state_binary_sensors_with_tilted(
    hass: HomeAssistant,
    client,
    hoppe_ehandle_connectsense_state,
) -> None:
    """Test Opening state creates Open and Tilt binary sensors when supported."""
    node = Node(
        client,
        _set_opening_state_metadata_states(
            hoppe_ehandle_connectsense_state,
            {"0": "Closed", "1": "Open", "2": "Tilted"},
        ),
    )
    client.driver.controller.nodes[node.node_id] = node

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    open_entity_id = "binary_sensor.ehandle_connectsense"
    tilted_entity_id = "binary_sensor.ehandle_connectsense_tilt"

    open_state = hass.states.get(open_entity_id)
    tilted_state = hass.states.get(tilted_entity_id)
    assert open_state is not None
    assert tilted_state is not None
    assert open_state.attributes[ATTR_DEVICE_CLASS] == BinarySensorDeviceClass.DOOR
    assert ATTR_DEVICE_CLASS not in tilted_state.attributes
    assert open_state.state == STATE_OFF
    assert tilted_state.state == STATE_OFF

    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Notification",
                    "commandClass": 113,
                    "endpoint": 0,
                    "property": "Access Control",
                    "propertyKey": "Opening state",
                    "newValue": 1,
                    "prevValue": 0,
                    "propertyName": "Access Control",
                    "propertyKeyName": "Opening state",
                },
            },
        )
    )
    await hass.async_block_till_done()

    assert hass.states.get(open_entity_id).state == STATE_ON
    assert hass.states.get(tilted_entity_id).state == STATE_OFF

    node.receive_event(
        Event(
            type="value updated",
            data={
                "source": "node",
                "event": "value updated",
                "nodeId": node.node_id,
                "args": {
                    "commandClassName": "Notification",
                    "commandClass": 113,
                    "endpoint": 0,
                    "property": "Access Control",
                    "propertyKey": "Opening state",
                    "newValue": 2,
                    "prevValue": 1,
                    "propertyName": "Access Control",
                    "propertyKeyName": "Opening state",
                },
            },
        )
    )
    await hass.async_block_till_done()

    assert hass.states.get(open_entity_id).state == STATE_ON
    assert hass.states.get(tilted_entity_id).state == STATE_ON