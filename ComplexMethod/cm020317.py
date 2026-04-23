async def test_event_order(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    auth,
    subscriber,
    setup_platform,
) -> None:
    """Test multiple events are in descending timestamp order."""
    await setup_platform()

    auth.responses = [
        aiohttp.web.json_response(GENERATE_IMAGE_URL_RESPONSE),
        aiohttp.web.Response(body=IMAGE_BYTES_FROM_EVENT),
        aiohttp.web.json_response(GENERATE_IMAGE_URL_RESPONSE),
        aiohttp.web.Response(body=IMAGE_BYTES_FROM_EVENT),
    ]
    event_session_id1 = "FWWVQVUdGNUlTU2V4MGV2aTNXV..."
    event_timestamp1 = dt_util.now()
    await subscriber.async_receive_event(
        create_event(
            event_session_id1,
            EVENT_ID + "1",
            PERSON_EVENT,
            timestamp=event_timestamp1,
        )
    )
    await hass.async_block_till_done()

    event_session_id2 = "GXXWRWVeHNUlUU3V3MGV3bUOYW..."
    event_timestamp2 = event_timestamp1 + datetime.timedelta(seconds=5)
    await subscriber.async_receive_event(
        create_event(
            event_session_id2,
            EVENT_ID + "2",
            MOTION_EVENT,
            timestamp=event_timestamp2,
        ),
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1
    camera = hass.states.get("camera.front")
    assert camera is not None

    device = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device
    assert device.name == DEVICE_NAME

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert browse.domain == DOMAIN
    assert browse.identifier == device.id
    assert browse.title == "Front: Recent Events"
    assert browse.can_expand

    # Motion event is most recent
    assert len(browse.children) == 2
    assert browse.children[0].domain == DOMAIN
    event_timestamp_string = event_timestamp2.strftime(DATE_STR_FORMAT)
    assert browse.children[0].title == f"Motion @ {event_timestamp_string}"
    assert not browse.children[0].can_expand
    assert not browse.children[0].can_play

    # Person event is next
    assert browse.children[1].domain == DOMAIN
    event_timestamp_string = event_timestamp1.strftime(DATE_STR_FORMAT)
    assert browse.children[1].title == f"Person @ {event_timestamp_string}"
    assert not browse.children[1].can_expand
    assert not browse.children[1].can_play