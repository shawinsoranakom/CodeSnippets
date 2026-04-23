def _check_state(hass: HomeAssistant, category: str, entity_id: str) -> None:
    event_index = CATEGORIES_TO_EVENTS[category]
    event = TEST_EVENTS[event_index]
    state = hass.states.get(entity_id)
    assert state.state == dt_util.parse_datetime(event.time).isoformat()
    assert state.attributes["category_id"] == event.category_id
    assert state.attributes["category_name"] == event.category_name
    assert state.attributes["type_id"] == event.type_id
    assert state.attributes["type_name"] == event.type_name
    assert state.attributes["name"] == event.name
    assert state.attributes["text"] == event.text
    assert state.attributes["partition_id"] == event.partition_id
    assert state.attributes["zone_id"] == event.zone_id
    assert state.attributes["user_id"] == event.user_id
    assert state.attributes["group"] == event.group
    assert state.attributes["priority"] == event.priority
    assert state.attributes["raw"] == event.raw
    if event_index == 2:
        assert state.attributes["zone_entity_id"] == "binary_sensor.zone_1"
    else:
        assert "zone_entity_id" not in state.attributes