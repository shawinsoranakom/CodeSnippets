async def test_open_cover_without_position(
    hass_hue: HomeAssistant, hue_client: TestClient
) -> None:
    """Test opening cover ."""
    cover_id = "cover.living_room_window"
    # Close cover first
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

    # Go through the API to turn it on
    cover_result = await perform_put_light_state(hass_hue, hue_client, cover_id, True)

    assert cover_result.status == HTTPStatus.OK
    assert CONTENT_TYPE_JSON in cover_result.headers["content-type"]

    for _ in range(11):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass_hue, future)
        await hass_hue.async_block_till_done()

    cover_result_json = await cover_result.json()

    assert len(cover_result_json) == 1

    # Check to make sure the state changed
    cover_test_2 = hass_hue.states.get(cover_id)
    assert cover_test_2.state == "open"
    assert cover_test_2.attributes.get("current_position") == 100

    # Go through the API to turn it off
    cover_result = await perform_put_light_state(hass_hue, hue_client, cover_id, False)

    assert cover_result.status == HTTPStatus.OK
    assert CONTENT_TYPE_JSON in cover_result.headers["content-type"]

    for _ in range(11):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass_hue, future)
        await hass_hue.async_block_till_done()

    cover_result_json = await cover_result.json()

    assert len(cover_result_json) == 1

    # Check to make sure the state changed
    cover_test_2 = hass_hue.states.get(cover_id)
    assert cover_test_2.state == "closed"
    assert cover_test_2.attributes.get("current_position") == 0