async def test_remove_entity_on_value_removed(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    zp3111: Node,
    client: MagicMock,
    integration: MockConfigEntry,
) -> None:
    """Test that when entity primary values are removed the entity becomes unavailable."""
    idle_cover_status_button_entity = (
        "button.4_in_1_sensor_idle_home_security_cover_status"
    )

    state = hass.states.get(idle_cover_status_button_entity)
    assert state
    assert state.state != STATE_UNAVAILABLE

    # check for expected entities
    binary_cover_entity = "binary_sensor.4_in_1_sensor_tampering_product_cover_removed"
    state = hass.states.get(binary_cover_entity)
    assert state
    assert state.state != STATE_UNAVAILABLE

    battery_level_entity = "sensor.4_in_1_sensor_battery_level"
    state = hass.states.get(battery_level_entity)
    assert state
    assert state.state != STATE_UNAVAILABLE

    unavailable_entities = {
        state.entity_id
        for state in hass.states.async_all()
        if state.state == STATE_UNAVAILABLE
    }

    # This value ID removal does not remove any entity
    event = Event(
        type="value removed",
        data={
            "source": "node",
            "event": "value removed",
            "nodeId": zp3111.node_id,
            "args": {
                "commandClassName": "Wake Up",
                "commandClass": 132,
                "endpoint": 0,
                "property": "wakeUpInterval",
                "prevValue": 3600,
                "propertyName": "wakeUpInterval",
            },
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    assert all(state != STATE_UNAVAILABLE for state in hass.states.async_all())

    # This value ID removal only affects the battery level entity
    event = Event(
        type="value removed",
        data={
            "source": "node",
            "event": "value removed",
            "nodeId": zp3111.node_id,
            "args": {
                "commandClassName": "Battery",
                "commandClass": 128,
                "endpoint": 0,
                "property": "level",
                "prevValue": 100,
                "propertyName": "level",
            },
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    state = hass.states.get(battery_level_entity)
    assert state
    assert state.state == STATE_UNAVAILABLE

    # This value ID removal affects its multiple notification sensors
    event = Event(
        type="value removed",
        data={
            "source": "node",
            "event": "value removed",
            "nodeId": zp3111.node_id,
            "args": {
                "commandClassName": "Notification",
                "commandClass": 113,
                "endpoint": 0,
                "property": "Home Security",
                "propertyKey": "Cover status",
                "prevValue": 0,
                "propertyName": "Home Security",
                "propertyKeyName": "Cover status",
            },
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    state = hass.states.get(binary_cover_entity)
    assert state
    assert state.state == STATE_UNAVAILABLE

    state = hass.states.get(idle_cover_status_button_entity)
    assert state
    assert state.state == STATE_UNAVAILABLE

    # existing entities and the entities with removed values should be unavailable
    new_unavailable_entities = {
        state.entity_id
        for state in hass.states.async_all()
        if state.state == STATE_UNAVAILABLE
    }
    assert (
        unavailable_entities
        | {
            battery_level_entity,
            binary_cover_entity,
            idle_cover_status_button_entity,
        }
        == new_unavailable_entities
    )

    # Entities should still be in the entity registry (not fully removed)
    assert entity_registry.async_get(battery_level_entity) is not None
    assert entity_registry.async_get(binary_cover_entity) is not None
    assert entity_registry.async_get(idle_cover_status_button_entity) is not None