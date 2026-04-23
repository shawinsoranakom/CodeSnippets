async def test_sensor_add_update(hass: HomeAssistant, mock_bridge_v2: Mock) -> None:
    """Test Event entity for newly added Relative Rotary resource."""
    await mock_bridge_v2.api.load_test_data([FAKE_DEVICE, FAKE_ZIGBEE_CONNECTIVITY])
    await setup_platform(hass, mock_bridge_v2, Platform.EVENT)

    test_entity_id = "event.hue_mocked_device_rotary"

    # verify entity does not exist before we start
    assert hass.states.get(test_entity_id) is None

    # Add new fake relative_rotary entity by emitting event
    mock_bridge_v2.api.emit_event("add", FAKE_ROTARY)
    await hass.async_block_till_done()

    # the entity should now be available
    state = hass.states.get(test_entity_id)
    assert state is not None
    assert state.state == "unknown"
    assert state.name == "Hue mocked device Rotary"
    # check event_types
    assert state.attributes[ATTR_EVENT_TYPES] == ["clock_wise", "counter_clock_wise"]

    # test update of entity works on incoming event
    btn_event = {
        "id": "fake_relative_rotary",
        "relative_rotary": {
            "rotary_report": {
                "action": "repeat",
                "rotation": {
                    "direction": "counter_clock_wise",
                    "steps": 60,
                    "duration": 400,
                },
                "updated": "2023-09-27T10:06:41.822Z",
            }
        },
        "type": "relative_rotary",
    }
    mock_bridge_v2.api.emit_event("update", btn_event)
    await hass.async_block_till_done()
    state = hass.states.get(test_entity_id)
    assert state.attributes[ATTR_EVENT_TYPE] == "counter_clock_wise"
    assert state.attributes["action"] == "repeat"
    assert state.attributes["steps"] == 60
    assert state.attributes["duration"] == 400