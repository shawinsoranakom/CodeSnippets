async def test_preset_mode_fan(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test fan discovery.

    This one has preset modes.
    """
    device = (
        "fan.test_7",
        "off",
        {
            "friendly_name": "Test fan 7",
            "supported_features": 8,
            "preset_modes": ["auto", "eco", "smart", "whoosh"],
            "preset_mode": "auto",
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "fan#test_7"
    assert appliance["displayCategories"][0] == "FAN"
    assert appliance["friendlyName"] == "Test fan 7"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.EndpointHealth",
        "Alexa.ModeController",
        "Alexa.PowerController",
        "Alexa",
    )

    range_capability = get_capability(capabilities, "Alexa.ModeController")
    assert range_capability is not None
    assert range_capability["instance"] == "fan.preset_mode"

    properties = range_capability["properties"]
    assert properties["nonControllable"] is False
    assert {"name": "mode"} in properties["supported"]

    capability_resources = range_capability["capabilityResources"]
    assert capability_resources is not None
    assert {
        "@type": "asset",
        "value": {"assetId": "Alexa.Setting.Preset"},
    } in capability_resources["friendlyNames"]

    configuration = range_capability["configuration"]
    assert configuration is not None

    call, _ = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "fan#test_7",
        "fan.set_preset_mode",
        hass,
        payload={"mode": "preset_mode.eco"},
        instance="fan.preset_mode",
    )
    assert call.data["preset_mode"] == "eco"

    call, _ = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "fan#test_7",
        "fan.set_preset_mode",
        hass,
        payload={"mode": "preset_mode.whoosh"},
        instance="fan.preset_mode",
    )
    assert call.data["preset_mode"] == "whoosh"

    with pytest.raises(AssertionError):
        await assert_request_calls_service(
            "Alexa.ModeController",
            "SetMode",
            "fan#test_7",
            "fan.set_preset_mode",
            hass,
            payload={"mode": "preset_mode.invalid"},
            instance="fan.preset_mode",
        )
    assert "Entity 'fan.test_7' does not support Preset 'invalid'" in caplog.text
    caplog.clear()