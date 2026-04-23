async def test_report_state_fan(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test proactive state reports with fan instance."""
    aioclient_mock.post(TEST_URL, text="", status=202)

    hass.states.async_set(
        "fan.test_fan",
        "off",
        {
            "friendly_name": "Test fan",
            "supported_features": 15,
            "oscillating": False,
            "preset_mode": None,
            "preset_modes": ["auto", "smart"],
            "percentage": None,
        },
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "fan.test_fan",
        "on",
        {
            "friendly_name": "Test fan",
            "supported_features": 15,
            "oscillating": True,
            "preset_mode": "smart",
            "preset_modes": ["auto", "smart"],
            "percentage": 90,
        },
    )

    # To trigger event listener
    await hass.async_block_till_done()

    assert len(aioclient_mock.mock_calls) == 1
    call = aioclient_mock.mock_calls

    call_json = call[0][2]
    assert call_json["event"]["header"]["namespace"] == "Alexa"
    assert call_json["event"]["header"]["name"] == "ChangeReport"

    change_reports = call_json["event"]["payload"]["change"]["properties"]

    checks = 0
    for report in change_reports:
        if report["name"] == "toggleState":
            assert report["value"] == "ON"
            assert report["instance"] == "fan.oscillating"
            assert report["namespace"] == "Alexa.ToggleController"
            checks += 1
        if report["name"] == "mode":
            assert report["value"] == "preset_mode.smart"
            assert report["instance"] == "fan.preset_mode"
            assert report["namespace"] == "Alexa.ModeController"
            checks += 1
        if report["name"] == "rangeValue":
            assert report["value"] == 90
            assert report["instance"] == "fan.percentage"
            assert report["namespace"] == "Alexa.RangeController"
            checks += 1
    assert checks == 3

    assert call_json["event"]["endpoint"]["endpointId"] == "fan#test_fan"