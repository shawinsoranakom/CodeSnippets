async def test_camera_event_clip_preview(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    auth,
    hass_client: ClientSessionGenerator,
    mp4,
    subscriber,
    setup_platform,
) -> None:
    """Test an event for a battery camera video clip."""
    # Capture any events published
    received_events = async_capture_events(hass, NEST_EVENT)
    await setup_platform()

    auth.responses = [
        aiohttp.web.Response(body=mp4.getvalue()),
    ]
    event_timestamp = dt_util.now()
    await subscriber.async_receive_event(
        create_event_message(
            create_battery_event_data(MOTION_EVENT),
            timestamp=event_timestamp,
        )
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1
    camera = hass.states.get("camera.front")
    assert camera is not None

    device = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device
    assert device.name == DEVICE_NAME

    # Verify events are published correctly
    assert len(received_events) == 1
    received_event = received_events[0]
    assert received_event.data["device_id"] == device.id
    assert received_event.data["type"] == "camera_motion"
    event_identifier = received_event.data["nest_event_id"]

    # List devices
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")
    assert browse.domain == DOMAIN
    assert len(browse.children) == 1
    assert browse.children[0].domain == DOMAIN
    assert browse.children[0].identifier == device.id
    assert browse.children[0].title == "Front: Recent Events"
    assert (
        browse.children[0].thumbnail
        == f"/api/nest/event_media/{device.id}/{event_identifier}/thumbnail"
    )
    assert browse.children[0].can_play
    # Browse to the device
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert browse.domain == DOMAIN
    assert browse.identifier == device.id
    assert browse.title == "Front: Recent Events"
    assert browse.can_expand
    assert not browse.thumbnail
    # The device expands recent events
    assert len(browse.children) == 1
    assert browse.children[0].domain == DOMAIN
    assert browse.children[0].identifier == f"{device.id}/{event_identifier}"
    event_timestamp_string = event_timestamp.strftime(DATE_STR_FORMAT)
    assert browse.children[0].title == f"Motion @ {event_timestamp_string}"
    assert not browse.children[0].can_expand
    assert len(browse.children[0].children) == 0
    assert browse.children[0].can_play
    assert (
        browse.children[0].thumbnail
        == f"/api/nest/event_media/{device.id}/{event_identifier}/thumbnail"
    )

    # Verify received event and media ids match
    assert browse.children[0].identifier == f"{device.id}/{event_identifier}"

    # Browse to the event
    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{device.id}/{event_identifier}"
    )
    assert browse.domain == DOMAIN
    event_timestamp_string = event_timestamp.strftime(DATE_STR_FORMAT)
    assert browse.title == f"Motion @ {event_timestamp_string}"
    assert not browse.can_expand
    assert len(browse.children) == 0
    assert browse.can_play

    # Resolving the event links to the media
    media = await async_resolve_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{device.id}/{event_identifier}", None
    )
    assert media.url == f"/api/nest/event_media/{device.id}/{event_identifier}"
    assert media.mime_type == "video/mp4"

    client = await hass_client()
    response = await client.get(media.url)
    assert response.status == HTTPStatus.OK, f"Response not matched: {response}"
    contents = await response.read()
    assert contents == mp4.getvalue()

    # Verify thumbnail for mp4 clip
    response = await client.get(
        f"/api/nest/event_media/{device.id}/{event_identifier}/thumbnail"
    )
    assert response.status == HTTPStatus.OK, f"Response not matched: {response}"
    await response.read()