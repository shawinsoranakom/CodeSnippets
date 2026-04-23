async def test_entity_config(hass: HomeAssistant) -> None:
    """Test that we can configure things via entity config."""
    request = get_new_request("Alexa.Discovery", "Discover")

    hass.states.async_set("light.test_1", "on", {"friendly_name": "Test light 1"})
    hass.states.async_set("scene.test_1", "scening", {"friendly_name": "Test 1"})

    alexa_config = MockConfig(hass)
    alexa_config.entity_config = {
        "light.test_1": {
            "name": "Config *name*",
            "display_categories": "SWITCH",
            "description": "Config >!<description",
        },
        "scene.test_1": {"description": "Config description"},
    }

    msg = await smart_home.async_handle_message(hass, alexa_config, request)

    assert "event" in msg
    msg = msg["event"]

    assert len(msg["payload"]["endpoints"]) == 2

    appliance = msg["payload"]["endpoints"][0]
    assert appliance["endpointId"] == "light#test_1"
    assert appliance["displayCategories"][0] == "SWITCH"
    assert appliance["friendlyName"] == "Config name"
    assert appliance["description"] == "Config description via Home Assistant"
    assert_endpoint_capabilities(
        appliance, "Alexa.PowerController", "Alexa.EndpointHealth", "Alexa"
    )

    scene = msg["payload"]["endpoints"][1]
    assert scene["endpointId"] == "scene#test_1"
    assert scene["displayCategories"][0] == "SCENE_TRIGGER"
    assert scene["friendlyName"] == "Test 1"
    assert scene["description"] == "Config description via Home Assistant (Scene)"