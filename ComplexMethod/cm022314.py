async def test_binary_sensor_add_update(
    hass: HomeAssistant, mock_bridge_v2: Mock
) -> None:
    """Test if binary_sensor get added/updated from events."""
    await mock_bridge_v2.api.load_test_data([FAKE_DEVICE, FAKE_ZIGBEE_CONNECTIVITY])
    await setup_platform(hass, mock_bridge_v2, Platform.BINARY_SENSOR)

    test_entity_id = "binary_sensor.hue_mocked_device_motion"

    # verify entity does not exist before we start
    assert hass.states.get(test_entity_id) is None

    # Add new fake sensor by emitting event
    mock_bridge_v2.api.emit_event("add", FAKE_BINARY_SENSOR)
    await hass.async_block_till_done()

    # the entity should now be available
    test_entity = hass.states.get(test_entity_id)
    assert test_entity is not None
    assert test_entity.state == "off"

    # test update of entity works on incoming event
    updated_sensor = {**FAKE_BINARY_SENSOR, "motion": {"motion": True}}
    mock_bridge_v2.api.emit_event("update", updated_sensor)
    await hass.async_block_till_done()
    test_entity = hass.states.get(test_entity_id)
    assert test_entity is not None
    assert test_entity.state == "on"
    # NEW: prefer motion_report.motion when present (should turn on even if plain motion is False)
    updated_sensor = {
        **FAKE_BINARY_SENSOR,
        "motion": {
            "motion": False,
            "motion_report": {"changed": "2025-01-01T00:00:00Z", "motion": True},
        },
    }
    mock_bridge_v2.api.emit_event("update", updated_sensor)
    await hass.async_block_till_done()
    assert hass.states.get(test_entity_id).state == "on"

    # NEW: motion_report False should turn it off (even if plain motion is True)
    updated_sensor = {
        **FAKE_BINARY_SENSOR,
        "motion": {
            "motion": True,
            "motion_report": {"changed": "2025-01-01T00:00:01Z", "motion": False},
        },
    }
    mock_bridge_v2.api.emit_event("update", updated_sensor)
    await hass.async_block_till_done()
    assert hass.states.get(test_entity_id).state == "off"