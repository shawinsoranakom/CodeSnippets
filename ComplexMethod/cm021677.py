async def test_button(hass: HomeAssistant, domain: str) -> None:
    """Test button discovery."""
    device = (
        f"{domain}.ring_doorbell",
        STATE_UNKNOWN,
        {"friendly_name": "Ring Doorbell"},
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == f"{domain}#ring_doorbell"
    assert appliance["displayCategories"][0] == "ACTIVITY_TRIGGER"
    assert appliance["friendlyName"] == "Ring Doorbell"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.SceneController",
        "Alexa.EventDetectionSensor",
        "Alexa.EndpointHealth",
        "Alexa",
    )
    scene_capability = get_capability(capabilities, "Alexa.SceneController")
    assert scene_capability["supportsDeactivation"] is False

    await assert_scene_controller_works(
        f"{domain}#ring_doorbell",
        f"{domain}.press",
        False,
        hass,
        "2022-04-19T07:53:05Z",
    )

    event_detection_capability = get_capability(
        capabilities, "Alexa.EventDetectionSensor"
    )
    assert event_detection_capability is not None
    properties = event_detection_capability["properties"]
    assert properties["proactivelyReported"] is True
    assert not properties["retrievable"]
    assert {"name": "humanPresenceDetectionState"} in properties["supported"]
    assert (
        event_detection_capability["configuration"]["detectionModes"]["humanPresence"][
            "supportsNotDetected"
        ]
        is False
    )