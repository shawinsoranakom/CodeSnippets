async def test_presence_sensor(hass: HomeAssistant) -> None:
    """Test presence sensor."""
    device = (
        "binary_sensor.test_presence_sensor",
        "off",
        {"friendly_name": "Test presence sensor", "device_class": "presence"},
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "binary_sensor#test_presence_sensor"
    assert appliance["displayCategories"][0] == "CAMERA"
    assert appliance["friendlyName"] == "Test presence sensor"

    capabilities = assert_endpoint_capabilities(
        appliance, "Alexa", "Alexa.EventDetectionSensor", "Alexa.EndpointHealth"
    )

    event_detection_capability = get_capability(
        capabilities, "Alexa.EventDetectionSensor"
    )
    assert event_detection_capability is not None
    properties = event_detection_capability["properties"]
    assert properties["proactivelyReported"] is True
    assert not properties["retrievable"]
    assert {"name": "humanPresenceDetectionState"} in properties["supported"]