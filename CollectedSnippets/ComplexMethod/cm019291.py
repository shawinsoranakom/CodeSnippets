async def test_invalid_service_calls(hass: HomeAssistant) -> None:
    """Test invalid service call arguments get discarded."""
    add_entities = MagicMock()
    await group.async_setup_platform(
        hass, {"name": "test", "entities": ["light.test1", "light.test2"]}, add_entities
    )
    await async_setup_component(hass, "light", {})
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    assert add_entities.call_count == 1
    grouped_light = add_entities.call_args[0][0][0]
    grouped_light.hass = hass

    service_call_events = async_capture_events(hass, EVENT_CALL_SERVICE)

    await grouped_light.async_turn_on(brightness=150, four_oh_four="404")
    data = {ATTR_ENTITY_ID: ["light.test1", "light.test2"], ATTR_BRIGHTNESS: 150}
    assert len(service_call_events) == 1
    service_event_call: Event = service_call_events[0]
    assert service_event_call.data["domain"] == LIGHT_DOMAIN
    assert service_event_call.data["service"] == SERVICE_TURN_ON
    assert service_event_call.data["service_data"] == data
    service_call_events.clear()

    await grouped_light.async_turn_off(transition=4, four_oh_four="404")
    data = {ATTR_ENTITY_ID: ["light.test1", "light.test2"], ATTR_TRANSITION: 4}
    assert len(service_call_events) == 1
    service_event_call: Event = service_call_events[0]
    assert service_event_call.data["domain"] == LIGHT_DOMAIN
    assert service_event_call.data["service"] == SERVICE_TURN_OFF
    assert service_event_call.data["service_data"] == data
    service_call_events.clear()

    data = {
        ATTR_BRIGHTNESS: 150,
        ATTR_COLOR_TEMP_KELVIN: 1234,
        ATTR_TRANSITION: 4,
    }
    await grouped_light.async_turn_on(**data)
    data[ATTR_ENTITY_ID] = ["light.test1", "light.test2"]
    service_event_call: Event = service_call_events[0]
    assert service_event_call.data["domain"] == LIGHT_DOMAIN
    assert service_event_call.data["service"] == SERVICE_TURN_ON
    assert service_event_call.data["service_data"] == data
    service_call_events.clear()