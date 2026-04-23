async def test_set_position_cover(
    hass_hue: HomeAssistant, hue_client: TestClient
) -> None:
    """Test setting position cover ."""
    cover_id = "cover.living_room_window"
    cover_number = ENTITY_NUMBERS_BY_ID[cover_id]
    # Turn the office light off first
    await hass_hue.services.async_call(
        cover.DOMAIN,
        const.SERVICE_CLOSE_COVER,
        {const.ATTR_ENTITY_ID: cover_id},
        blocking=True,
    )

    cover_test = hass_hue.states.get(cover_id)
    assert cover_test.state == "closing"

    for _ in range(7):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass_hue, future)
        await hass_hue.async_block_till_done()

    cover_test = hass_hue.states.get(cover_id)
    assert cover_test.state == "closed"

    cover_json = await perform_get_light_state(
        hue_client, "cover.living_room_window", HTTPStatus.OK
    )
    assert cover_json["state"][HUE_API_STATE_ON] is False
    assert cover_json["state"][HUE_API_STATE_BRI] == 1

    level = 20
    brightness = round(level / 100 * 254)

    # Go through the API to open
    cover_result = await perform_put_light_state(
        hass_hue, hue_client, cover_id, False, brightness=brightness
    )

    assert cover_result.status == HTTPStatus.OK
    assert CONTENT_TYPE_JSON in cover_result.headers["content-type"]

    cover_result_json = await cover_result.json()

    assert len(cover_result_json) == 2
    assert True, cover_result_json[0]["success"][f"/lights/{cover_number}/state/on"]
    assert cover_result_json[1]["success"][f"/lights/{cover_number}/state/bri"] == level

    for _ in range(100):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass_hue, future)
        await hass_hue.async_block_till_done()

    # Check to make sure the state changed
    cover_test_2 = hass_hue.states.get(cover_id)
    assert cover_test_2.state == "open"
    assert cover_test_2.attributes.get("current_position") == level