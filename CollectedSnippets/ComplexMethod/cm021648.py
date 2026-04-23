async def test_lock(hass: HomeAssistant) -> None:
    """Test lock discovery."""
    device = ("lock.test", "off", {"friendly_name": "Test lock"})
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "lock#test"
    assert appliance["displayCategories"][0] == "SMARTLOCK"
    assert appliance["friendlyName"] == "Test lock"
    assert_endpoint_capabilities(
        appliance, "Alexa.LockController", "Alexa.EndpointHealth", "Alexa"
    )

    _, msg = await assert_request_calls_service(
        "Alexa.LockController", "Lock", "lock#test", "lock.lock", hass
    )

    properties = msg["context"]["properties"][0]
    assert properties["name"] == "lockState"
    assert properties["namespace"] == "Alexa.LockController"
    assert properties["value"] == "LOCKED"

    _, msg = await assert_request_calls_service(
        "Alexa.LockController", "Unlock", "lock#test", "lock.unlock", hass
    )

    properties = msg["context"]["properties"][0]
    assert properties["name"] == "lockState"
    assert properties["namespace"] == "Alexa.LockController"
    assert properties["value"] == "UNLOCKED"