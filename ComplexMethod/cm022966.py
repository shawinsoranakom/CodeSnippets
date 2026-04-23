async def test_cct_light(hass: HomeAssistant, mock_wled: MagicMock) -> None:
    """Test CCT support for WLED."""
    assert (state := hass.states.get("light.wled_cct_light"))
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_SUPPORTED_COLOR_MODES) == [
        ColorMode.COLOR_TEMP,
        ColorMode.RGBW,
    ]
    assert state.attributes.get(ATTR_COLOR_MODE) == ColorMode.COLOR_TEMP
    assert state.attributes.get(ATTR_MIN_COLOR_TEMP_KELVIN) == 2000
    assert state.attributes.get(ATTR_MAX_COLOR_TEMP_KELVIN) == 6535
    assert state.attributes.get(ATTR_COLOR_TEMP_KELVIN) == 2942

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.wled_cct_light",
            ATTR_COLOR_TEMP_KELVIN: 4321,
        },
        blocking=True,
    )
    assert mock_wled.segment.call_count == 1
    mock_wled.segment.assert_called_with(
        cct=130,
        on=True,
        segment_id=0,
    )