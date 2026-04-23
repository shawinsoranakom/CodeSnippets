async def test_variable_fan(hass: HomeAssistant) -> None:
    """Test fan discovery.

    This one has variable speed.
    """
    device = (
        "fan.test_2",
        "off",
        {
            "friendly_name": "Test fan 2",
            "supported_features": 1,
            "percentage": 100,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "fan#test_2"
    assert appliance["displayCategories"][0] == "FAN"
    assert appliance["friendlyName"] == "Test fan 2"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.RangeController",
        "Alexa.PowerController",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    capability = get_capability(capabilities, "Alexa.RangeController")
    assert capability is not None

    capability = get_capability(capabilities, "Alexa.PowerController")
    assert capability is not None

    call, _ = await assert_request_calls_service(
        "Alexa.RangeController",
        "SetRangeValue",
        "fan#test_2",
        "fan.set_percentage",
        hass,
        payload={"rangeValue": "50"},
        instance="fan.percentage",
    )
    assert call.data["percentage"] == 50

    call, _ = await assert_request_calls_service(
        "Alexa.RangeController",
        "SetRangeValue",
        "fan#test_2",
        "fan.set_percentage",
        hass,
        payload={"rangeValue": "33"},
        instance="fan.percentage",
    )
    assert call.data["percentage"] == 33

    call, _ = await assert_request_calls_service(
        "Alexa.RangeController",
        "SetRangeValue",
        "fan#test_2",
        "fan.set_percentage",
        hass,
        payload={"rangeValue": "100"},
        instance="fan.percentage",
    )
    assert call.data["percentage"] == 100

    await assert_range_changes(
        hass,
        [
            (95, -5, False),
            (100, 5, False),
            (20, -80, False),
            (66, -34, False),
            (80, -1, True),
            (20, -4, True),
        ],
        "Alexa.RangeController",
        "AdjustRangeValue",
        "fan#test_2",
        "fan.set_percentage",
        "percentage",
        "fan.percentage",
    )
    await assert_range_changes(
        hass,
        [
            (0, -100, False),
        ],
        "Alexa.RangeController",
        "AdjustRangeValue",
        "fan#test_2",
        "fan.turn_off",
        None,
        "fan.percentage",
    )