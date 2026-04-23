async def test_put_light_state(
    hass: HomeAssistant, hass_hue: HomeAssistant, hue_client: TestClient
) -> None:
    """Test the setting of light states."""
    await perform_put_test_on_ceiling_lights(hass_hue, hue_client)

    # Turn the bedroom light on first
    await hass_hue.services.async_call(
        light.DOMAIN,
        const.SERVICE_TURN_ON,
        {const.ATTR_ENTITY_ID: "light.ceiling_lights", light.ATTR_BRIGHTNESS: 153},
        blocking=True,
    )

    ceiling_lights = hass_hue.states.get("light.ceiling_lights")
    assert ceiling_lights.state == STATE_ON
    assert ceiling_lights.attributes[light.ATTR_BRIGHTNESS] == 153

    # update light state through api
    await perform_put_light_state(
        hass_hue,
        hue_client,
        "light.ceiling_lights",
        True,
        hue=4369,
        saturation=127,
        brightness=128,
    )

    assert (
        hass.states.get("light.ceiling_lights").attributes[light.ATTR_BRIGHTNESS] == 129
    )

    # update light state through api
    await perform_put_light_state(
        hass_hue,
        hue_client,
        "light.ceiling_lights",
        True,
        hue=4369,
        saturation=127,
        brightness=123,
    )

    assert (
        hass.states.get("light.ceiling_lights").attributes[light.ATTR_BRIGHTNESS] == 123
    )

    # go through api to get the state back
    ceiling_json = await perform_get_light_state(
        hue_client, "light.ceiling_lights", HTTPStatus.OK
    )
    assert ceiling_json["state"][HUE_API_STATE_BRI] == 123
    assert ceiling_json["state"][HUE_API_STATE_HUE] == 4369
    assert ceiling_json["state"][HUE_API_STATE_SAT] == 127

    # update light state through api
    await perform_put_light_state(
        hass_hue,
        hue_client,
        "light.ceiling_lights",
        True,
        hue=4369,
        saturation=127,
        brightness=255,
    )

    # go through api to get the state back
    ceiling_json = await perform_get_light_state(
        hue_client, "light.ceiling_lights", HTTPStatus.OK
    )
    assert ceiling_json["state"][HUE_API_STATE_BRI] == 254
    assert ceiling_json["state"][HUE_API_STATE_HUE] == 4369
    assert ceiling_json["state"][HUE_API_STATE_SAT] == 127

    # update light state through api
    await perform_put_light_state(
        hass_hue,
        hue_client,
        "light.ceiling_lights",
        True,
        brightness=100,
        xy=((0.488, 0.48)),
    )

    # go through api to get the state back
    ceiling_json = await perform_get_light_state(
        hue_client, "light.ceiling_lights", HTTPStatus.OK
    )
    assert ceiling_json["state"][HUE_API_STATE_BRI] == 100
    assert hass.states.get("light.ceiling_lights").attributes[light.ATTR_XY_COLOR] == (
        (0.488, 0.48)
    )

    # Go through the API to turn it off
    ceiling_result = await perform_put_light_state(
        hass_hue, hue_client, "light.ceiling_lights", False
    )

    ceiling_result_json = await ceiling_result.json()

    assert ceiling_result.status == HTTPStatus.OK
    assert CONTENT_TYPE_JSON in ceiling_result.headers["content-type"]

    assert len(ceiling_result_json) == 1

    # Check to make sure the state changed
    ceiling_lights = hass_hue.states.get("light.ceiling_lights")
    assert ceiling_lights.state == STATE_OFF
    ceiling_json = await perform_get_light_state(
        hue_client, "light.ceiling_lights", HTTPStatus.OK
    )
    # Removed assert HUE_API_STATE_BRI == 0 as Hue API states bri must be 1..254
    assert ceiling_json["state"][HUE_API_STATE_HUE] == 0
    assert ceiling_json["state"][HUE_API_STATE_SAT] == 0

    # Make sure we can't change the bedroom light state
    bedroom_result = await perform_put_light_state(
        hass_hue, hue_client, "light.bed_light", True
    )
    assert bedroom_result.status == HTTPStatus.UNAUTHORIZED

    # Make sure we can't change the kitchen light state
    kitchen_result = await perform_put_light_state(
        hass_hue, hue_client, "light.kitchen_lights", True
    )
    assert kitchen_result.status == HTTPStatus.UNAUTHORIZED

    # Turn the ceiling lights on first and color temp.
    await hass_hue.services.async_call(
        light.DOMAIN,
        const.SERVICE_TURN_ON,
        {
            const.ATTR_ENTITY_ID: "light.ceiling_lights",
            light.ATTR_COLOR_TEMP_KELVIN: 50000,
        },
        blocking=True,
    )

    await perform_put_light_state(
        hass_hue, hue_client, "light.ceiling_lights", True, color_temp=50
    )

    assert (
        hass_hue.states.get("light.ceiling_lights").attributes[
            light.ATTR_COLOR_TEMP_KELVIN
        ]
        == 20000
    )

    # mock light.turn_on call
    attributes = hass.states.get("light.ceiling_lights").attributes
    supported_features = (
        attributes[ATTR_SUPPORTED_FEATURES] | light.LightEntityFeature.TRANSITION
    )
    attributes = {**attributes, ATTR_SUPPORTED_FEATURES: supported_features}
    hass.states.async_set("light.ceiling_lights", STATE_ON, attributes)
    call_turn_on = async_mock_service(hass, "light", "turn_on")

    # update light state through api
    await perform_put_light_state(
        hass_hue,
        hue_client,
        "light.ceiling_lights",
        True,
        brightness=99,
        xy=((0.488, 0.48)),
        transitiontime=60,
    )

    await hass.async_block_till_done()
    assert call_turn_on[0]
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == ["light.ceiling_lights"]
    assert call_turn_on[0].data[light.ATTR_BRIGHTNESS] == 99
    assert call_turn_on[0].data[light.ATTR_XY_COLOR] == ((0.488, 0.48))
    assert call_turn_on[0].data[light.ATTR_TRANSITION] == 6