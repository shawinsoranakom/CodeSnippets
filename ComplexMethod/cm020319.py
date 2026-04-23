async def test_multiple_clip_preview_events_in_session(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    auth,
    hass_client: ClientSessionGenerator,
    subscriber,
    setup_platform,
) -> None:
    """Test multiple events published within the same event session."""
    await setup_platform()

    event_timestamp1 = dt_util.now()
    event_timestamp2 = event_timestamp1 + datetime.timedelta(seconds=5)

    assert len(hass.states.async_all()) == 1
    camera = hass.states.get("camera.front")
    assert camera is not None

    device = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device
    assert device.name == DEVICE_NAME

    # Capture any events published
    received_events = async_capture_events(hass, NEST_EVENT)

    # Publish two events: First motion, then a person is recognized. Both
    # events share a single clip.
    auth.responses = [
        aiohttp.web.Response(body=IMAGE_BYTES_FROM_EVENT),
    ]
    await subscriber.async_receive_event(
        create_event_message(
            create_battery_event_data(MOTION_EVENT),
            timestamp=event_timestamp1,
        )
    )
    await hass.async_block_till_done()
    await subscriber.async_receive_event(
        create_event_message(
            create_battery_event_data(PERSON_EVENT),
            timestamp=event_timestamp2,
        )
    )
    await hass.async_block_till_done()

    assert len(received_events) == 2
    received_event = received_events[0]
    assert received_event.data["device_id"] == device.id
    assert received_event.data["type"] == "camera_motion"
    event_identifier1 = received_event.data["nest_event_id"]
    received_event = received_events[1]
    assert received_event.data["device_id"] == device.id
    assert received_event.data["type"] == "camera_person"
    event_identifier2 = received_event.data["nest_event_id"]

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert browse.domain == DOMAIN
    assert browse.identifier == device.id
    assert browse.title == "Front: Recent Events"
    assert browse.can_expand

    # The two distinct events are combined in a single clip preview
    assert len(browse.children) == 1
    event = browse.children[0]
    assert event.domain == DOMAIN
    event_timestamp_string = event_timestamp1.strftime(DATE_STR_FORMAT)
    assert event.identifier == f"{device.id}/{event_identifier2}"
    assert event.title == f"Motion, Person @ {event_timestamp_string}"
    assert not event.can_expand
    assert event.can_play

    # Resolve media for each event that was published and they will resolve
    # to the same clip preview media clip object.
    # Resolve media for the first event
    media = await async_resolve_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{device.id}/{event_identifier1}", None
    )
    assert media.url == f"/api/nest/event_media/{device.id}/{event_identifier1}"
    assert media.mime_type == "video/mp4"

    client = await hass_client()
    response = await client.get(media.url)
    assert response.status == HTTPStatus.OK, f"Response not matched: {response}"
    contents = await response.read()
    assert contents == IMAGE_BYTES_FROM_EVENT

    # Resolve media for the second event
    media = await async_resolve_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{device.id}/{event_identifier1}", None
    )
    assert media.url == f"/api/nest/event_media/{device.id}/{event_identifier1}"
    assert media.mime_type == "video/mp4"

    response = await client.get(media.url)
    assert response.status == HTTPStatus.OK, f"Response not matched: {response}"
    contents = await response.read()
    assert contents == IMAGE_BYTES_FROM_EVENT