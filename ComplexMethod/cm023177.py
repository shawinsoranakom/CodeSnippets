async def test_smoke_co_notification_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    zcombo_smoke_co_alarm: Node,
    integration: MockConfigEntry,
) -> None:
    """Test smoke and CO notification sensors with diagnostic states."""
    # Test smoke alarm sensor
    smoke_sensor = "binary_sensor.zcombo_g_smoke_co_alarm_smoke_detected"
    state = hass.states.get(smoke_sensor)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_DEVICE_CLASS] == BinarySensorDeviceClass.SMOKE
    entity_entry = entity_registry.async_get(smoke_sensor)
    assert entity_entry
    assert entity_entry.entity_category != EntityCategory.DIAGNOSTIC

    # Test smoke alarm diagnostic sensor
    smoke_diagnostic = "binary_sensor.zcombo_g_smoke_co_alarm_smoke_alarm_test"
    state = hass.states.get(smoke_diagnostic)
    assert state
    assert state.state == STATE_OFF
    entity_entry = entity_registry.async_get(smoke_diagnostic)
    assert entity_entry
    assert entity_entry.entity_category == EntityCategory.DIAGNOSTIC

    # Test CO alarm sensor
    co_sensor = "binary_sensor.zcombo_g_smoke_co_alarm_carbon_monoxide_detected"
    state = hass.states.get(co_sensor)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_DEVICE_CLASS] == BinarySensorDeviceClass.CO
    entity_entry = entity_registry.async_get(co_sensor)
    assert entity_entry
    assert entity_entry.entity_category != EntityCategory.DIAGNOSTIC

    # Test diagnostic entities
    entity_ids = [
        "binary_sensor.zcombo_g_smoke_co_alarm_smoke_alarm_test",
        "binary_sensor.zcombo_g_smoke_co_alarm_alarm_silenced",
        "binary_sensor.zcombo_g_smoke_co_alarm_replacement_required_end_of_life",
        "binary_sensor.zcombo_g_smoke_co_alarm_alarm_silenced_2",
        "binary_sensor.zcombo_g_smoke_co_alarm_system_hardware_failure",
        "binary_sensor.zcombo_g_smoke_co_alarm_low_battery_level",
    ]
    for entity_id in entity_ids:
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry
        assert entity_entry.entity_category == EntityCategory.DIAGNOSTIC

    # Test that no idle states are created as entities
    entity_id = "binary_sensor.zcombo_g_smoke_co_alarm_idle"
    state = hass.states.get(entity_id)
    assert state is None
    entity_entry = entity_registry.async_get(entity_id)
    assert entity_entry is None

    # Test state updates for smoke alarm
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 3,
            "args": {
                "commandClassName": "Notification",
                "commandClass": 113,
                "endpoint": 0,
                "property": "Smoke Alarm",
                "propertyKey": "Sensor status",
                "newValue": 2,
                "prevValue": 0,
                "propertyName": "Smoke Alarm",
                "propertyKeyName": "Sensor status",
            },
        },
    )
    zcombo_smoke_co_alarm.receive_event(event)
    await hass.async_block_till_done()  # Wait for state change to be processed
    # Get a fresh state after the sleep
    state = hass.states.get(smoke_sensor)
    assert state is not None, "Smoke sensor state should not be None"
    assert state.state == STATE_ON, (
        f"Expected smoke sensor state to be 'on', got '{state.state}'"
    )

    # Test state updates for CO alarm
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 3,
            "args": {
                "commandClassName": "Notification",
                "commandClass": 113,
                "endpoint": 0,
                "property": "CO Alarm",
                "propertyKey": "Sensor status",
                "newValue": 2,
                "prevValue": 0,
                "propertyName": "CO Alarm",
                "propertyKeyName": "Sensor status",
            },
        },
    )
    zcombo_smoke_co_alarm.receive_event(event)
    await hass.async_block_till_done()  # Wait for state change to be processed
    # Get a fresh state after the sleep
    state = hass.states.get(co_sensor)
    assert state is not None, "CO sensor state should not be None"
    assert state.state == STATE_ON, (
        f"Expected CO sensor state to be 'on', got '{state.state}'"
    )

    # Test diagnostic state updates for smoke alarm
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 3,
            "args": {
                "commandClassName": "Notification",
                "commandClass": 113,
                "endpoint": 0,
                "property": "Smoke Alarm",
                "propertyKey": "Alarm status",
                "newValue": 3,
                "prevValue": 0,
                "propertyName": "Smoke Alarm",
                "propertyKeyName": "Alarm status",
            },
        },
    )
    zcombo_smoke_co_alarm.receive_event(event)
    await hass.async_block_till_done()  # Wait for state change to be processed
    # Get a fresh state after the sleep
    state = hass.states.get(smoke_diagnostic)
    assert state is not None, "Smoke diagnostic state should not be None"
    assert state.state == STATE_ON, (
        f"Expected smoke diagnostic state to be 'on', got '{state.state}'"
    )