async def test_scene_updates(
    hass: HomeAssistant, mock_bridge_v2: Mock, v2_resources_test_data: JsonArrayType
) -> None:
    """Test scene events from bridge."""
    await mock_bridge_v2.api.load_test_data(v2_resources_test_data)

    await setup_platform(hass, mock_bridge_v2, Platform.SCENE)

    test_entity_id = "scene.test_room_mocked_scene"

    # verify entity does not exist before we start
    assert hass.states.get(test_entity_id) is None

    # Add new fake scene
    mock_bridge_v2.api.emit_event("add", FAKE_SCENE)
    await hass.async_block_till_done()

    # the entity should now be available
    test_entity = hass.states.get(test_entity_id)
    assert test_entity is not None
    assert test_entity.state == STATE_UNKNOWN
    assert test_entity.name == "Test Room Mocked Scene"
    assert test_entity.attributes["brightness"] == 166

    # test update
    updated_resource = {**FAKE_SCENE}
    updated_resource["actions"][0]["action"]["dimming"]["brightness"] = 35.0
    mock_bridge_v2.api.emit_event("update", updated_resource)
    await hass.async_block_till_done()
    test_entity = hass.states.get(test_entity_id)
    assert test_entity is not None
    assert test_entity.attributes["brightness"] == 89

    # # test entity name changes on group name change
    mock_bridge_v2.api.emit_event(
        "update",
        {
            "type": "room",
            "id": "6ddc9066-7e7d-4a03-a773-c73937968296",
            "metadata": {"name": "Test Room 2"},
        },
    )
    await hass.async_block_till_done()
    test_entity = hass.states.get(test_entity_id)
    assert test_entity.attributes["group_name"] == "Test Room 2"

    # # test delete
    mock_bridge_v2.api.emit_event("delete", updated_resource)
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    test_entity = hass.states.get(test_entity_id)
    assert test_entity is None