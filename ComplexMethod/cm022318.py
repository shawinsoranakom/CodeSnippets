async def test_switch(
    hass: HomeAssistant, mock_bridge_v2: Mock, v2_resources_test_data: JsonArrayType
) -> None:
    """Test if (config) switches get created."""
    await mock_bridge_v2.api.load_test_data(v2_resources_test_data)

    await setup_platform(hass, mock_bridge_v2, Platform.SWITCH)
    # there shouldn't have been any requests at this point
    assert len(mock_bridge_v2.mock_requests) == 0
    # 4 entities should be created from test data
    assert len(hass.states.async_all()) == 4

    # test config switch to enable/disable motion sensor
    test_entity = hass.states.get("switch.hue_motion_sensor_motion_sensor_enabled")
    assert test_entity is not None
    assert test_entity.name == "Hue motion sensor Motion sensor enabled"
    assert test_entity.state == "on"
    assert test_entity.attributes["device_class"] == "switch"

    # test config switch to enable/disable a behavior_instance resource (=builtin automation)
    test_entity = hass.states.get("switch.philips_hue_automation_timer_test")
    assert test_entity is not None
    assert test_entity.name == "Philips hue Automation: Timer Test"
    assert test_entity.state == "on"
    assert test_entity.attributes["device_class"] == "switch"