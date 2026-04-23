async def test_media_store_save_filesystem_error(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    auth,
    hass_client: ClientSessionGenerator,
    subscriber,
    setup_platform,
) -> None:
    """Test a filesystem error writing event media."""
    await setup_platform()

    auth.responses = [
        aiohttp.web.Response(body=IMAGE_BYTES_FROM_EVENT),
    ]
    event_timestamp = dt_util.now()
    # The client fetches the media from the server, but has a failure when
    # persisting the media to disk.
    client = await hass_client()
    with patch("homeassistant.components.nest.media_source.open", side_effect=OSError):
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

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert browse.domain == DOMAIN
    assert browse.identifier == device.id
    assert len(browse.children) == 1
    event = browse.children[0]

    media = await async_resolve_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{event.identifier}", None
    )
    assert media.url == f"/api/nest/event_media/{event.identifier}"
    assert media.mime_type == "video/mp4"

    # We fail to retrieve the media from the server since the origin filesystem op failed
    client = await hass_client()
    response = await client.get(media.url)
    assert response.status == HTTPStatus.NOT_FOUND, f"Response not matched: {response}"