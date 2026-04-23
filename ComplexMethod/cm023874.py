async def test_put_light_state_fan(
    hass_hue: HomeAssistant, hue_client: TestClient
) -> None:
    """Test turning on fan and setting speed."""
    # Turn the fan off first
    await hass_hue.services.async_call(
        fan.DOMAIN,
        const.SERVICE_TURN_OFF,
        {const.ATTR_ENTITY_ID: "fan.living_room_fan"},
        blocking=True,
    )

    # Emulated hue converts 0-100% to 0-254.
    level = 43
    brightness = round(level * 254 / 100)

    fan_result = await perform_put_light_state(
        hass_hue, hue_client, "fan.living_room_fan", True, brightness=brightness
    )

    fan_result_json = await fan_result.json()

    assert fan_result.status == HTTPStatus.OK
    assert len(fan_result_json) == 2

    living_room_fan = hass_hue.states.get("fan.living_room_fan")
    assert living_room_fan.state == "on"
    assert living_room_fan.attributes[fan.ATTR_PERCENTAGE] == 43

    # Check setting the brightness of a fan to 0, 33%, 66% and 100% will respectively turn it off, low, medium or high
    # We also check non-cached GET value to exercise the code.
    await perform_put_light_state(
        hass_hue, hue_client, "fan.living_room_fan", True, brightness=0
    )
    assert hass_hue.states.get("fan.living_room_fan").state == STATE_OFF
    await perform_put_light_state(
        hass_hue,
        hue_client,
        "fan.living_room_fan",
        True,
        brightness=round(33 * 254 / 100),
    )
    assert (
        hass_hue.states.get("fan.living_room_fan").attributes[fan.ATTR_PERCENTAGE] == 33
    )
    with patch.object(hue_api, "STATE_CACHED_TIMEOUT", 0.000001):
        await asyncio.sleep(0.000001)
        fan_json = await perform_get_light_state(
            hue_client, "fan.living_room_fan", HTTPStatus.OK
        )
        assert fan_json["state"][HUE_API_STATE_ON] is True
        assert round(fan_json["state"][HUE_API_STATE_BRI] * 100 / 254) == 33

    await perform_put_light_state(
        hass_hue,
        hue_client,
        "fan.living_room_fan",
        True,
        brightness=round(66 * 254 / 100),
    )
    assert (
        hass_hue.states.get("fan.living_room_fan").attributes[fan.ATTR_PERCENTAGE] == 66
    )
    with patch.object(hue_api, "STATE_CACHED_TIMEOUT", 0.000001):
        await asyncio.sleep(0.000001)
        fan_json = await perform_get_light_state(
            hue_client, "fan.living_room_fan", HTTPStatus.OK
        )
        assert fan_json["state"][HUE_API_STATE_ON] is True
        assert (
            round(fan_json["state"][HUE_API_STATE_BRI] * 100 / 254) == 66
        )  # small rounding error in inverse operation

    await perform_put_light_state(
        hass_hue,
        hue_client,
        "fan.living_room_fan",
        True,
        brightness=round(100 * 254 / 100),
    )
    assert (
        hass_hue.states.get("fan.living_room_fan").attributes[fan.ATTR_PERCENTAGE]
        == 100
    )
    with patch.object(hue_api, "STATE_CACHED_TIMEOUT", 0.000001):
        await asyncio.sleep(0.000001)
        fan_json = await perform_get_light_state(
            hue_client, "fan.living_room_fan", HTTPStatus.OK
        )
        assert fan_json["state"][HUE_API_STATE_ON] is True
        assert round(fan_json["state"][HUE_API_STATE_BRI] * 100 / 254) == 100

    await perform_put_light_state(
        hass_hue,
        hue_client,
        "fan.living_room_fan",
        False,
        brightness=0,
    )
    assert (
        hass_hue.states.get("fan.living_room_fan").attributes[fan.ATTR_PERCENTAGE] == 0
    )
    with patch.object(hue_api, "STATE_CACHED_TIMEOUT", 0.000001):
        await asyncio.sleep(0.000001)
        fan_json = await perform_get_light_state(
            hue_client, "fan.living_room_fan", HTTPStatus.OK
        )
        assert fan_json["state"][HUE_API_STATE_ON] is False
        assert fan_json["state"][HUE_API_STATE_BRI] == 1