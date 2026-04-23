async def test_report_state_humidifier(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test proactive state reports with humidifier instance."""
    aioclient_mock.post(TEST_URL, text="", status=202)

    hass.states.async_set(
        "humidifier.test_humidifier",
        "off",
        {
            "friendly_name": "Test humidifier",
            "supported_features": 1,
            "mode": None,
            "available_modes": ["auto", "smart"],
        },
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        "humidifier.test_humidifier",
        "on",
        {
            "friendly_name": "Test humidifier",
            "supported_features": 1,
            "mode": "smart",
            "available_modes": ["auto", "smart"],
            "humidity": 55,
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
        if report["name"] == "mode":
            assert report["value"] == "mode.smart"
            assert report["instance"] == "humidifier.mode"
            assert report["namespace"] == "Alexa.ModeController"
            checks += 1
        if report["name"] == "rangeValue":
            assert report["value"] == 55
            assert report["instance"] == "humidifier.humidity"
            assert report["namespace"] == "Alexa.RangeController"
            checks += 1
    assert checks == 2

    assert call_json["event"]["endpoint"]["endpointId"] == "humidifier#test_humidifier"