async def test_event_clip_media_attachment(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    device_registry: dr.DeviceRegistry,
    subscriber,
    auth,
    setup_platform,
    mp4,
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

    # Set up fake media, and publish clip events
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

    assert len(received_events) == 1
    received_event = received_events[0]
    attachment = received_event.data.get("attachment")
    assert attachment
    assert list(attachment.keys()) == ["image", "video"]
    assert attachment["image"].startswith("/api/nest/event_media")
    assert attachment["image"].endswith("/thumbnail")
    assert attachment["video"].startswith("/api/nest/event_media")
    assert not attachment["video"].endswith("/thumbnail")

    # Download the attachment content and verify it works
    for content_path in attachment.values():
        client = await hass_client()
        response = await client.get(content_path)
        assert response.status == HTTPStatus.OK, f"Response not matched: {response}"
        await response.read()