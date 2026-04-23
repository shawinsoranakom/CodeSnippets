async def test_get_light_state_when_none(
    hass_hue: HomeAssistant, hue_client: TestClient
) -> None:
    """Test the getting of light state when brightness is None."""
    hass_hue.states.async_set(
        "light.ceiling_lights",
        STATE_ON,
        {
            light.ATTR_BRIGHTNESS: None,
            light.ATTR_RGB_COLOR: None,
            light.ATTR_HS_COLOR: None,
            light.ATTR_COLOR_TEMP_KELVIN: None,
            light.ATTR_XY_COLOR: None,
            light.ATTR_SUPPORTED_COLOR_MODES: [
                light.ColorMode.COLOR_TEMP,
                light.ColorMode.HS,
                light.ColorMode.XY,
            ],
            light.ATTR_COLOR_MODE: light.ColorMode.XY,
        },
    )

    light_json = await perform_get_light_state(
        hue_client, "light.ceiling_lights", HTTPStatus.OK
    )
    state = light_json["state"]
    assert state[HUE_API_STATE_ON] is True
    assert state[HUE_API_STATE_BRI] == 1
    assert state[HUE_API_STATE_HUE] == 0
    assert state[HUE_API_STATE_SAT] == 0
    assert state[HUE_API_STATE_CT] == 153

    hass_hue.states.async_set(
        "light.ceiling_lights",
        STATE_OFF,
        {
            light.ATTR_BRIGHTNESS: None,
            light.ATTR_RGB_COLOR: None,
            light.ATTR_HS_COLOR: None,
            light.ATTR_COLOR_TEMP_KELVIN: None,
            light.ATTR_XY_COLOR: None,
            light.ATTR_SUPPORTED_COLOR_MODES: [
                light.ColorMode.COLOR_TEMP,
                light.ColorMode.HS,
                light.ColorMode.XY,
            ],
            light.ATTR_COLOR_MODE: light.ColorMode.XY,
        },
    )

    light_json = await perform_get_light_state(
        hue_client, "light.ceiling_lights", HTTPStatus.OK
    )
    state = light_json["state"]
    assert state[HUE_API_STATE_ON] is False
    assert state[HUE_API_STATE_BRI] == 1
    assert state[HUE_API_STATE_HUE] == 0
    assert state[HUE_API_STATE_SAT] == 0
    assert state[HUE_API_STATE_CT] == 153