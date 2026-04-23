async def test_get_light_state(hass_hue: HomeAssistant, hue_client: TestClient) -> None:
    """Test the getting of light state."""
    # Turn ceiling lights on and set to 127 brightness, and set light color
    await hass_hue.services.async_call(
        light.DOMAIN,
        const.SERVICE_TURN_ON,
        {
            const.ATTR_ENTITY_ID: "light.ceiling_lights",
            light.ATTR_BRIGHTNESS: 127,
            light.ATTR_RGB_COLOR: (1, 2, 7),
        },
        blocking=True,
    )

    office_json = await perform_get_light_state(
        hue_client, "light.ceiling_lights", HTTPStatus.OK
    )

    assert office_json["state"][HUE_API_STATE_ON] is True
    assert office_json["state"][HUE_API_STATE_BRI] == 127
    assert office_json["state"][HUE_API_STATE_HUE] == 41869
    assert office_json["state"][HUE_API_STATE_SAT] == 217

    # Check all lights view
    result_json = await async_get_lights(hue_client)
    assert ENTITY_NUMBERS_BY_ID["light.ceiling_lights"] in result_json
    assert (
        result_json[ENTITY_NUMBERS_BY_ID["light.ceiling_lights"]]["state"][
            HUE_API_STATE_BRI
        ]
        == 127
    )

    # Turn office light off
    await hass_hue.services.async_call(
        light.DOMAIN,
        const.SERVICE_TURN_OFF,
        {const.ATTR_ENTITY_ID: "light.ceiling_lights"},
        blocking=True,
    )

    office_json = await perform_get_light_state(
        hue_client, "light.ceiling_lights", HTTPStatus.OK
    )

    assert office_json["state"][HUE_API_STATE_ON] is False
    # Removed assert HUE_API_STATE_BRI == 0 as Hue API states bri must be 1..254
    assert office_json["state"][HUE_API_STATE_HUE] == 0
    assert office_json["state"][HUE_API_STATE_SAT] == 0

    # Make sure bedroom light isn't accessible
    await perform_get_light_state(
        hue_client, "light.bed_light", HTTPStatus.UNAUTHORIZED
    )

    # Make sure kitchen light isn't accessible
    await perform_get_light_state(
        hue_client, "light.kitchen_lights", HTTPStatus.UNAUTHORIZED
    )