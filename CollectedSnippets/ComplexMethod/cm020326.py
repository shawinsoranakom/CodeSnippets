async def test_camera_event_media_eviction(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    auth,
    hass_client: ClientSessionGenerator,
    subscriber,
    setup_platform,
) -> None:
    """Test media files getting evicted from the cache."""
    await setup_platform()

    device = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device
    assert device.name == DEVICE_NAME

    # Browse to the device
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert browse.domain == DOMAIN
    assert browse.identifier == device.id
    assert browse.title == "Front: Recent Events"
    assert browse.can_expand

    # No events published yet
    assert len(browse.children) == 0

    event_timestamp = dt_util.now()
    for i in range(7):
        auth.responses = [aiohttp.web.Response(body=f"image-bytes-{i}".encode())]
        ts = event_timestamp + datetime.timedelta(seconds=i)
        await subscriber.async_receive_event(
            create_event_message(
                create_battery_event_data(
                    MOTION_EVENT, event_session_id=f"event-session-{i}"
                ),
                timestamp=ts,
            )
        )
    await hass.async_block_till_done()

    # Cache is limited to 5 events removing media as the cache is filled
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert len(browse.children) == 5

    auth.responses = [
        aiohttp.web.Response(body=b"image-bytes-7"),
    ]
    ts = event_timestamp + datetime.timedelta(seconds=8)
    # Simulate a failure case removing the media on cache eviction
    with patch(
        "homeassistant.components.nest.media_source.os.remove", side_effect=OSError
    ) as mock_remove:
        await subscriber.async_receive_event(
            create_event_message(
                create_battery_event_data(
                    MOTION_EVENT, event_session_id="event-session-7"
                ),
                timestamp=ts,
            )
        )
        await hass.async_block_till_done()
        assert mock_remove.called

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert len(browse.children) == 5
    child_events = iter(browse.children)

    # Verify all other content is still persisted correctly
    client = await hass_client()
    for i in reversed(range(3, 8)):
        child_event = next(child_events)
        response = await client.get(f"/api/nest/event_media/{child_event.identifier}")
        assert response.status == HTTPStatus.OK, f"Response not matched: {response}"
        contents = await response.read()
        assert contents == f"image-bytes-{i}".encode()
        await hass.async_block_till_done()