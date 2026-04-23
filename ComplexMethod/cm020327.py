async def test_camera_image_resize(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    auth,
    hass_client: ClientSessionGenerator,
    subscriber,
    setup_platform,
) -> None:
    """Test scaling a thumbnail for an event image."""
    await setup_platform()

    device = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device
    assert device.name == DEVICE_NAME

    # Capture any events published
    received_events = async_capture_events(hass, NEST_EVENT)

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

    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{device.id}/{event_identifier}"
    )
    assert browse.domain == DOMAIN
    assert browse.identifier == f"{device.id}/{event_identifier}"
    assert "Person" in browse.title
    assert not browse.can_expand
    assert not browse.children
    assert (
        browse.thumbnail
        == f"/api/nest/event_media/{device.id}/{event_identifier}/thumbnail"
    )

    client = await hass_client()
    response = await client.get(browse.thumbnail)
    assert response.status == HTTPStatus.OK, f"Response not matched: {response}"
    contents = await response.read()
    assert contents == IMAGE_BYTES_FROM_EVENT

    # The event thumbnail is used for the device thumbnail
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")
    assert browse.domain == DOMAIN
    assert len(browse.children) == 1
    assert browse.children[0].identifier == device.id
    assert browse.children[0].title == "Front: Recent Events"
    assert (
        browse.children[0].thumbnail
        == f"/api/nest/event_media/{device.id}/{event_identifier}/thumbnail"
    )
    assert browse.children[0].can_play

    # Browse to device. No thumbnail is needed for the device on the device page
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert browse.domain == DOMAIN
    assert browse.identifier == device.id
    assert browse.title == "Front: Recent Events"
    assert not browse.thumbnail
    assert len(browse.children) == 1