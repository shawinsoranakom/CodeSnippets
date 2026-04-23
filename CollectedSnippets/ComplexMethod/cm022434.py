async def test_brightness_light(hass: HomeAssistant, supported_color_modes) -> None:
    """Test brightness trait support for light domain."""
    assert helpers.get_google_type(light.DOMAIN, None) is not None
    assert trait.BrightnessTrait.supported(
        light.DOMAIN, 0, None, {"supported_color_modes": supported_color_modes}
    )

    trt = trait.BrightnessTrait(
        hass,
        State("light.bla", light.STATE_ON, {light.ATTR_BRIGHTNESS: 243}),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {}

    assert trt.query_attributes() == {"brightness": 95}

    events = async_capture_events(hass, EVENT_CALL_SERVICE)

    calls = async_mock_service(hass, light.DOMAIN, light.SERVICE_TURN_ON)
    await trt.execute(
        trait.COMMAND_BRIGHTNESS_ABSOLUTE, BASIC_DATA, {"brightness": 50}, {}
    )
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "light.bla", light.ATTR_BRIGHTNESS_PCT: 50}

    assert len(events) == 1
    assert events[0].data == {
        "domain": "light",
        "service": "turn_on",
        "service_data": {"brightness_pct": 50, "entity_id": "light.bla"},
    }