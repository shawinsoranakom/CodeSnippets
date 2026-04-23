async def test_put_then_get_cached_properly(
    hass: HomeAssistant, hass_hue: HomeAssistant, hue_client: TestClient
) -> None:
    """Test the setting of light states and an immediate readback reads the same values."""

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
        brightness=254,
    )

    # Check that a Hue brightness level of 254 becomes 255 in HA realm.
    assert (
        hass.states.get("light.ceiling_lights").attributes[light.ATTR_BRIGHTNESS] == 255
    )

    # Make sure that the GET response is the same as the PUT response within 2 seconds if the service call is successful and the state doesn't change.
    # We simulate a long latence for the actual setting of the entity by forcibly sitting different values directly.
    await hass_hue.services.async_call(
        light.DOMAIN,
        const.SERVICE_TURN_ON,
        {const.ATTR_ENTITY_ID: "light.ceiling_lights", light.ATTR_BRIGHTNESS: 153},
        blocking=True,
    )

    # go through api to get the state back, the value returned should match those set in the last PUT request.
    ceiling_json = await perform_get_light_state(
        hue_client, "light.ceiling_lights", HTTPStatus.OK
    )

    assert ceiling_json["state"][HUE_API_STATE_HUE] == 4369
    assert ceiling_json["state"][HUE_API_STATE_SAT] == 127
    assert ceiling_json["state"][HUE_API_STATE_BRI] == 254

    # Make sure that the GET response does not use the cache if PUT response within 2 seconds if the service call is Unsuccessful and the state does not change.
    await hass_hue.services.async_call(
        light.DOMAIN,
        const.SERVICE_TURN_OFF,
        {const.ATTR_ENTITY_ID: "light.ceiling_lights"},
        blocking=True,
    )

    # go through api to get the state back
    ceiling_json = await perform_get_light_state(
        hue_client, "light.ceiling_lights", HTTPStatus.OK
    )

    # Now it should be the real value as the state of the entity has changed to OFF.
    assert ceiling_json["state"][HUE_API_STATE_HUE] == 0
    assert ceiling_json["state"][HUE_API_STATE_SAT] == 0
    assert ceiling_json["state"][HUE_API_STATE_BRI] == 1

    # Ensure we read the actual value after exceeding the timeout time.

    # Turn the bedroom light back on first
    await hass_hue.services.async_call(
        light.DOMAIN,
        const.SERVICE_TURN_ON,
        {const.ATTR_ENTITY_ID: "light.ceiling_lights"},
        blocking=True,
    )

    # update light state through api
    await perform_put_light_state(
        hass_hue,
        hue_client,
        "light.ceiling_lights",
        True,
        hue=4369,
        saturation=127,
        brightness=254,
    )

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

    # go through api to get the state back, the value returned should match those set in the last PUT request.
    ceiling_json = await perform_get_light_state(
        hue_client, "light.ceiling_lights", HTTPStatus.OK
    )

    # With no wait, we must be reading what we set via the PUT call.
    assert ceiling_json["state"][HUE_API_STATE_HUE] == 4369
    assert ceiling_json["state"][HUE_API_STATE_SAT] == 127
    assert ceiling_json["state"][HUE_API_STATE_BRI] == 254

    with patch.object(hue_api, "STATE_CACHED_TIMEOUT", 0.000001):
        await asyncio.sleep(0.000001)

        # go through api to get the state back, the value returned should now match the actual values.
        ceiling_json = await perform_get_light_state(
            hue_client, "light.ceiling_lights", HTTPStatus.OK
        )

        # Once we're after the cached duration, we should see the real value.
        assert ceiling_json["state"][HUE_API_STATE_HUE] == 41869
        assert ceiling_json["state"][HUE_API_STATE_SAT] == 217
        assert ceiling_json["state"][HUE_API_STATE_BRI] == 127