async def test_input_number(hass: HomeAssistant, domain: str) -> None:
    """Test input_number and number discovery."""
    device = (
        f"{domain}.test_slider",
        30,
        {
            "initial": 30,
            "min": -20,
            "max": 35,
            "step": 1,
            "mode": "slider",
            "friendly_name": "Test Slider",
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == f"{domain}#test_slider"
    assert appliance["displayCategories"][0] == "OTHER"
    assert appliance["friendlyName"] == "Test Slider"

    capabilities = assert_endpoint_capabilities(
        appliance, "Alexa.RangeController", "Alexa.EndpointHealth", "Alexa"
    )

    range_capability = get_capability(
        capabilities, "Alexa.RangeController", f"{domain}.value"
    )

    capability_resources = range_capability["capabilityResources"]
    assert capability_resources is not None
    assert {
        "@type": "text",
        "value": {"text": "Value", "locale": "en-US"},
    } in capability_resources["friendlyNames"]

    configuration = range_capability["configuration"]
    assert configuration is not None

    supported_range = configuration["supportedRange"]
    assert supported_range["minimumValue"] == -20
    assert supported_range["maximumValue"] == 35
    assert supported_range["precision"] == 1

    presets = configuration["presets"]
    assert {
        "rangeValue": 35,
        "presetResources": {
            "friendlyNames": [
                {"@type": "asset", "value": {"assetId": "Alexa.Value.Maximum"}}
            ]
        },
    } in presets

    assert {
        "rangeValue": -20,
        "presetResources": {
            "friendlyNames": [
                {"@type": "asset", "value": {"assetId": "Alexa.Value.Minimum"}}
            ]
        },
    } in presets

    call, _ = await assert_request_calls_service(
        "Alexa.RangeController",
        "SetRangeValue",
        f"{domain}#test_slider",
        f"{domain}.set_value",
        hass,
        payload={"rangeValue": 10},
        instance=f"{domain}.value",
    )
    assert call.data["value"] == 10

    await assert_range_changes(
        hass,
        [(25, -5, False), (35, 5, False), (-20, -100, False), (35, 100, False)],
        "Alexa.RangeController",
        "AdjustRangeValue",
        f"{domain}#test_slider",
        f"{domain}.set_value",
        "value",
        instance=f"{domain}.value",
    )