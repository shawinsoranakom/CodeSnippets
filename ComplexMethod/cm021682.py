async def test_report_state_number(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    domain: str,
    value: float,
    unit: str | None,
    label: AlexaGlobalCatalog,
) -> None:
    """Test proactive state reports with number or input_number instance."""
    aioclient_mock.post(TEST_URL, text="", status=202)
    state = {
        "friendly_name": f"Test {domain}",
        "min": 10,
        "max": 100,
        "step": 0.1,
    }

    if unit:
        state["unit_of_measurement"] = unit

    hass.states.async_set(
        f"{domain}.test_{domain}",
        None,
        state,
    )

    await state_report.async_enable_proactive_mode(hass, get_default_config(hass))

    hass.states.async_set(
        f"{domain}.test_{domain}",
        value,
        state,
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
        if report["name"] == "connectivity":
            assert report["value"] == {"value": "OK"}
            assert report["namespace"] == "Alexa.EndpointHealth"
            checks += 1
        if report["name"] == "rangeValue":
            assert report["value"] == value
            assert report["instance"] == f"{domain}.value"
            assert report["namespace"] == "Alexa.RangeController"
            checks += 1
    assert checks == 2

    assert call_json["event"]["endpoint"]["endpointId"] == f"{domain}#test_{domain}"