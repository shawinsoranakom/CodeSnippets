async def test_turn_on_off_intent_valve(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test HassTurnOn/Off intent on valve domains."""
    assert await async_setup_component(hass, "intent", {})

    valve = entity_registry.async_get_or_create("valve", "test", "valve_uid")

    hass.states.async_set(valve.entity_id, "closed")
    open_calls = async_mock_service(hass, "valve", SERVICE_OPEN_VALVE)
    close_calls = async_mock_service(hass, "valve", SERVICE_CLOSE_VALVE)

    await intent.async_handle(
        hass, "test", "HassTurnOn", {"name": {"value": valve.entity_id}}
    )

    assert len(open_calls) == 1
    call = open_calls[0]
    assert call.domain == "valve"
    assert call.service == SERVICE_OPEN_VALVE
    assert call.data == {"entity_id": valve.entity_id}

    await intent.async_handle(
        hass, "test", "HassTurnOff", {"name": {"value": valve.entity_id}}
    )

    assert len(close_calls) == 1
    call = close_calls[0]
    assert call.domain == "valve"
    assert call.service == SERVICE_CLOSE_VALVE
    assert call.data == {"entity_id": valve.entity_id}