async def test_event_media_attachment(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    device_registry: dr.DeviceRegistry,
    subscriber,
    auth,
    setup_platform,
) -> None:
    """Verify that an event media attachment is successfully resolved."""
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
    attachment = received_event.data.get("attachment")
    assert attachment
    assert list(attachment.keys()) == ["image"]
    assert attachment["image"].startswith("/api/nest/event_media")
    assert attachment["image"].endswith("/thumbnail")

    # Download the attachment content and verify it works
    client = await hass_client()
    response = await client.get(attachment["image"])
    assert response.status == HTTPStatus.OK, f"Response not matched: {response}"
    await response.read()