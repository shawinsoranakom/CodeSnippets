async def test_scene(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_bridge_v2: Mock,
    v2_resources_test_data: JsonArrayType,
) -> None:
    """Test if (config) scenes get created."""
    await mock_bridge_v2.api.load_test_data(v2_resources_test_data)

    await setup_platform(hass, mock_bridge_v2, Platform.SCENE)
    # there shouldn't have been any requests at this point
    assert len(mock_bridge_v2.mock_requests) == 0
    # 3 entities should be created from test data
    assert len(hass.states.async_all()) == 3

    # test (dynamic) scene for a hue zone
    test_entity = hass.states.get("scene.test_zone_dynamic_test_scene")
    assert test_entity is not None
    assert test_entity.name == "Test Zone Dynamic Test Scene"
    assert test_entity.state == STATE_UNKNOWN
    assert test_entity.attributes["group_name"] == "Test Zone"
    assert test_entity.attributes["group_type"] == "zone"
    assert test_entity.attributes["name"] == "Dynamic Test Scene"
    assert test_entity.attributes["speed"] == 0.6269841194152832
    assert test_entity.attributes["brightness"] == 119
    assert test_entity.attributes["is_dynamic"] is True

    # test (regular) scene for a hue room
    test_entity = hass.states.get("scene.test_room_regular_test_scene")
    assert test_entity is not None
    assert test_entity.name == "Test Room Regular Test Scene"
    assert test_entity.state == STATE_UNKNOWN
    assert test_entity.attributes["group_name"] == "Test Room"
    assert test_entity.attributes["group_type"] == "room"
    assert test_entity.attributes["name"] == "Regular Test Scene"
    assert test_entity.attributes["speed"] == 0.5
    assert test_entity.attributes["brightness"] == 255
    assert test_entity.attributes["is_dynamic"] is False

    # test smart scene
    test_entity = hass.states.get("scene.test_room_smart_test_scene")
    assert test_entity is not None
    assert test_entity.name == "Test Room Smart Test Scene"
    assert test_entity.state == STATE_UNKNOWN
    assert test_entity.attributes["group_name"] == "Test Room"
    assert test_entity.attributes["group_type"] == "room"
    assert test_entity.attributes["name"] == "Smart Test Scene"
    assert test_entity.attributes["active_timeslot_id"] == 1
    assert test_entity.attributes["active_timeslot_name"] == "wednesday"
    assert test_entity.attributes["active_scene"] == "Regular Test Scene"
    assert test_entity.attributes["is_active"] is True

    # scene entities should have be assigned to the room/zone device/service
    for entity_id in (
        "scene.test_zone_dynamic_test_scene",
        "scene.test_room_regular_test_scene",
        "scene.test_room_smart_test_scene",
    ):
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry
        assert entity_entry.device_id is not None