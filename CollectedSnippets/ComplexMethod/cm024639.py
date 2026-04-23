async def test_light_basic_properties(hass: HomeAssistant) -> None:
    """Test the basic properties."""
    client = create_mock_client()
    client.priorities = [{const.KEY_PRIORITY: TEST_PRIORITY}]
    await setup_test_config_entry(hass, hyperion_client=client)

    entity_state = hass.states.get(TEST_ENTITY_ID_1)
    assert entity_state
    assert entity_state.state == "on"
    assert entity_state.attributes["brightness"] == 255
    assert entity_state.attributes["hs_color"] == (0.0, 0.0)
    assert entity_state.attributes["icon"] == hyperion_light.ICON_LIGHTBULB
    assert entity_state.attributes["effect"] == hyperion_light.KEY_EFFECT_SOLID

    # By default the effect list contains only 'Solid'.
    assert len(entity_state.attributes["effect_list"]) == 1

    assert entity_state.attributes["color_mode"] == ColorMode.HS
    assert entity_state.attributes["supported_color_modes"] == [ColorMode.HS]
    assert entity_state.attributes["supported_features"] == LightEntityFeature.EFFECT