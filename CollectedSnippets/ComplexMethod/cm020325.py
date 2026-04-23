async def test_media_store_load_filesystem_error(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    auth,
    hass_client: ClientSessionGenerator,
    subscriber,
    setup_platform,
) -> None:
    """Test a filesystem error reading event media."""
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    camera = hass.states.get("camera.front")
    assert camera is not None

    device = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device
    assert device.name == DEVICE_NAME

    # Capture any events published
    received_events = async_capture_events(hass, NEST_EVENT)

    auth.responses = [
        aiohttp.web.Response(body=IMAGE_BYTES_FROM_EVENT),
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
    assert received_event.data["device_id"] == device.id
    assert received_event.data["type"] == "camera_motion"
    event_identifier = received_event.data["nest_event_id"]

    client = await hass_client()

    # Fetch the media from the server, and simluate a failure reading from disk
    client = await hass_client()
    with patch("homeassistant.components.nest.media_source.open", side_effect=OSError):
        response = await client.get(
            f"/api/nest/event_media/{device.id}/{event_identifier}"
        )
        assert response.status == HTTPStatus.NOT_FOUND, (
            f"Response not matched: {response}"
        )