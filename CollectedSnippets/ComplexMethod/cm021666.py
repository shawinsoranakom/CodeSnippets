async def test_motion_sensor_event_detection(hass: HomeAssistant) -> None:
    """Test motion sensor with EventDetectionSensor discovery."""
    device = (
        "binary_sensor.test_motion_camera_event",
        "off",
        {"friendly_name": "Test motion camera event", "device_class": "motion"},
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "binary_sensor#test_motion_camera_event"
    assert appliance["displayCategories"][0] == "CAMERA"
    assert appliance["friendlyName"] == "Test motion camera event"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa",
        "Alexa.MotionSensor",
        "Alexa.EventDetectionSensor",
        "Alexa.EndpointHealth",
    )

    event_detection_capability = get_capability(
        capabilities, "Alexa.EventDetectionSensor"
    )
    assert event_detection_capability is not None
    properties = event_detection_capability["properties"]
    assert properties["proactivelyReported"] is True
    assert not properties["retrievable"]
    assert {"name": "humanPresenceDetectionState"} in properties["supported"]