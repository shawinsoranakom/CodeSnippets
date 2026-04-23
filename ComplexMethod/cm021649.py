async def test_media_player_inputs(hass: HomeAssistant) -> None:
    """Test media player discovery with source list inputs."""
    device = (
        "media_player.test",
        "on",
        {
            "friendly_name": "Test media player",
            "supported_features": MediaPlayerEntityFeature.SELECT_SOURCE,
            "volume_level": 0.75,
            "source_list": [
                "foo",
                "foo_2",
                "hdmi",
                "hdmi_2",
                "hdmi-3",
                "hdmi4",
                "hdmi 5",
                "HDMI 6",
                "hdmi_arc",
                "aux",
                "input 1",
                "tv",
                0,
                None,
            ],
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "media_player#test"
    assert appliance["displayCategories"][0] == "TV"
    assert appliance["friendlyName"] == "Test media player"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa",
        "Alexa.InputController",
        "Alexa.PowerController",
        "Alexa.EndpointHealth",
    )

    input_capability = get_capability(capabilities, "Alexa.InputController")
    assert input_capability is not None
    assert {"name": "AUX"} not in input_capability["inputs"]
    assert {"name": "AUX 1"} in input_capability["inputs"]
    assert {"name": "HDMI 1"} in input_capability["inputs"]
    assert {"name": "HDMI 2"} in input_capability["inputs"]
    assert {"name": "HDMI 3"} in input_capability["inputs"]
    assert {"name": "HDMI 4"} in input_capability["inputs"]
    assert {"name": "HDMI 5"} in input_capability["inputs"]
    assert {"name": "HDMI 6"} in input_capability["inputs"]
    assert {"name": "HDMI ARC"} in input_capability["inputs"]
    assert {"name": "FOO 1"} not in input_capability["inputs"]
    assert {"name": "TV"} in input_capability["inputs"]

    call, _ = await assert_request_calls_service(
        "Alexa.InputController",
        "SelectInput",
        "media_player#test",
        "media_player.select_source",
        hass,
        payload={"input": "HDMI 1"},
    )
    assert call.data["source"] == "hdmi"

    call, _ = await assert_request_calls_service(
        "Alexa.InputController",
        "SelectInput",
        "media_player#test",
        "media_player.select_source",
        hass,
        payload={"input": "HDMI 2"},
    )
    assert call.data["source"] == "hdmi_2"

    call, _ = await assert_request_calls_service(
        "Alexa.InputController",
        "SelectInput",
        "media_player#test",
        "media_player.select_source",
        hass,
        payload={"input": "HDMI 5"},
    )
    assert call.data["source"] == "hdmi 5"

    call, _ = await assert_request_calls_service(
        "Alexa.InputController",
        "SelectInput",
        "media_player#test",
        "media_player.select_source",
        hass,
        payload={"input": "HDMI 6"},
    )
    assert call.data["source"] == "HDMI 6"

    call, _ = await assert_request_calls_service(
        "Alexa.InputController",
        "SelectInput",
        "media_player#test",
        "media_player.select_source",
        hass,
        payload={"input": "TV"},
    )
    assert call.data["source"] == "tv"