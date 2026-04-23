async def test_camera_event(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    device_registry: dr.DeviceRegistry,
    subscriber,
    auth,
    setup_platform,
) -> None:
    """Test a media source and image created for an event."""
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    camera = hass.states.get("camera.front")
    assert camera is not None

    device = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device
    assert device.name == DEVICE_NAME

    # Capture any events published
    received_events = async_capture_events(hass, NEST_EVENT)

    # Set up fake media, and publish image events
    auth.responses = [
        aiohttp.web.json_response(GENERATE_IMAGE_URL_RESPONSE),
        aiohttp.web.Response(body=IMAGE_BYTES_FROM_EVENT),
    ]
    event_timestamp = dt_util.now()
    await subscriber.async_receive_event(
        create_event(
            EVENT_SESSION_ID,
            EVENT_ID,
            PERSON_EVENT,
            timestamp=event_timestamp,
        )
    )
    await hass.async_block_till_done()

    assert len(received_events) == 1
    received_event = received_events[0]
    assert received_event.data["device_id"] == device.id
    assert received_event.data["type"] == "camera_person"
    event_identifier = received_event.data["nest_event_id"]

    # Media root directory
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")
    assert browse.title == "Nest"
    assert browse.identifier == ""
    assert browse.can_expand
    # A device is represented as a child directory
    assert len(browse.children) == 1
    assert browse.children[0].domain == DOMAIN
    assert browse.children[0].identifier == device.id
    assert browse.children[0].title == "Front: Recent Events"
    assert browse.children[0].can_expand
    assert browse.children[0].can_play
    # Expanding the root does not expand the device
    assert len(browse.children[0].children) == 0

    # Browse to the device
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert browse.domain == DOMAIN
    assert browse.identifier == device.id
    assert browse.title == "Front: Recent Events"
    assert browse.can_expand
    # The device expands recent events
    assert len(browse.children) == 1
    assert browse.children[0].domain == DOMAIN
    assert browse.children[0].identifier == f"{device.id}/{event_identifier}"
    event_timestamp_string = event_timestamp.strftime(DATE_STR_FORMAT)
    assert browse.children[0].title == f"Person @ {event_timestamp_string}"
    assert not browse.children[0].can_expand
    assert len(browse.children[0].children) == 0

    # Browse to the event
    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{device.id}/{event_identifier}"
    )
    assert browse.domain == DOMAIN
    assert browse.identifier == f"{device.id}/{event_identifier}"
    assert "Person" in browse.title
    assert not browse.can_expand
    assert not browse.children
    assert not browse.can_play

    # Resolving the event links to the media
    media = await async_resolve_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{device.id}/{event_identifier}", None
    )
    assert media.url == f"/api/nest/event_media/{device.id}/{event_identifier}"
    assert media.mime_type == "image/jpeg"

    client = await hass_client()
    response = await client.get(media.url)
    assert response.status == HTTPStatus.OK, f"Response not matched: {response}"
    contents = await response.read()
    assert contents == IMAGE_BYTES_FROM_EVENT

    # Resolving the device id points to the most recent event
    media = await async_resolve_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}", None)
    assert media.url == f"/api/nest/event_media/{device.id}/{event_identifier}"
    assert media.mime_type == "image/jpeg"