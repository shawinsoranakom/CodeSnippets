async def test_controller_status_sensor(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, client, integration
) -> None:
    """Test controller status sensor is created and gets updated on controller state changes."""
    entity_id = "sensor.z_stick_gen5_usb_controller_status"
    entity_entry = entity_registry.async_get(entity_id)

    assert not entity_entry.disabled
    assert entity_entry.entity_category is EntityCategory.DIAGNOSTIC
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "ready"

    event = Event(
        "status changed",
        data={"source": "controller", "event": "status changed", "status": 1},
    )
    client.driver.controller.receive_event(event)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "unresponsive"

    # Test transitions work
    event = Event(
        "status changed",
        data={"source": "controller", "event": "status changed", "status": 2},
    )
    client.driver.controller.receive_event(event)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "jammed"

    # Disconnect the client and make sure the entity is still available
    await client.disconnect()
    assert hass.states.get(entity_id).state != STATE_UNAVAILABLE