async def test_event_media_failure(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    auth,
    hass_client: ClientSessionGenerator,
    subscriber,
    setup_platform,
) -> None:
    """Test event media fetch sees a failure from the server."""
    received_events = async_capture_events(hass, NEST_EVENT)

    await setup_platform()
    # Failure from server when fetching media
    auth.responses = [
        aiohttp.web.Response(status=HTTPStatus.INTERNAL_SERVER_ERROR),
    ]
    event_timestamp = dt_util.now()
    await subscriber.async_receive_event(
        create_event(
            EVENT_SESSION_ID,
            EVENT_ID,
            PERSON_EVENT,
            timestamp=event_timestamp,
        ),
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
    assert received_event.data["type"] == "camera_person"
    event_identifier = received_event.data["nest_event_id"]

    # Resolving the event links to the media
    media = await async_resolve_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{device.id}/{event_identifier}", None
    )
    assert media.url == f"/api/nest/event_media/{device.id}/{event_identifier}"
    assert media.mime_type == "image/jpeg"

    # Media is not available to be fetched
    client = await hass_client()
    response = await client.get(media.url)
    assert response.status == HTTPStatus.NOT_FOUND, f"Response not matched: {response}"