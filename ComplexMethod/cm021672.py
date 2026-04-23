async def test_input_number_float(hass: HomeAssistant, domain: str) -> None:
    """Test input_number and number discovery."""
    device = (
        f"{domain}.test_slider_float",
        0.5,
        {
            "initial": 0.5,
            "min": 0,
            "max": 1,
            "step": 0.01,
            "mode": "slider",
            "friendly_name": "Test Slider Float",
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == f"{domain}#test_slider_float"
    assert appliance["displayCategories"][0] == "OTHER"
    assert appliance["friendlyName"] == "Test Slider Float"

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
    assert supported_range["minimumValue"] == 0
    assert supported_range["maximumValue"] == 1
    assert supported_range["precision"] == 0.01

    presets = configuration["presets"]
    assert {
        "rangeValue": 1,
        "presetResources": {
            "friendlyNames": [
                {"@type": "asset", "value": {"assetId": "Alexa.Value.Maximum"}}
            ]
        },
    } in presets

    assert {
        "rangeValue": 0,
        "presetResources": {
            "friendlyNames": [
                {"@type": "asset", "value": {"assetId": "Alexa.Value.Minimum"}}
            ]
        },
    } in presets

    call, _ = await assert_request_calls_service(
        "Alexa.RangeController",
        "SetRangeValue",
        f"{domain}#test_slider_float",
        f"{domain}.set_value",
        hass,
        payload={"rangeValue": 0.333},
        instance=f"{domain}.value",
    )
    assert call.data["value"] == 0.333

    await assert_range_changes(
        hass,
        [
            (0.4, -0.1, False),
            (0.6, 0.1, False),
            (0, -100, False),
            (1, 100, False),
            (0.51, 0.01, False),
        ],
        "Alexa.RangeController",
        "AdjustRangeValue",
        f"{domain}#test_slider_float",
        f"{domain}.set_value",
        "value",
        instance=f"{domain}.value",
    )