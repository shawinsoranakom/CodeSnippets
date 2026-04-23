async def test_media_store_persistence(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    auth,
    hass_client: ClientSessionGenerator,
    event_store,
    subscriber,
    setup_platform,
    config_entry,
) -> None:
    """Test the disk backed media store persistence."""
    await setup_platform()

    device = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device
    assert device.name == DEVICE_NAME

    auth.responses = [
        aiohttp.web.Response(body=IMAGE_BYTES_FROM_EVENT),
    ]
    event_timestamp = dt_util.now()
    await subscriber.async_receive_event(
        create_event_message(
            create_battery_event_data(MOTION_EVENT), timestamp=event_timestamp
        )
    )
    await hass.async_block_till_done()

    # Browse to event
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert len(browse.children) == 1
    assert browse.children[0].domain == DOMAIN
    event_timestamp_string = event_timestamp.strftime(DATE_STR_FORMAT)
    assert browse.children[0].title == f"Motion @ {event_timestamp_string}"
    assert not browse.children[0].can_expand
    assert browse.children[0].can_play
    event_identifier = browse.children[0].identifier

    media = await async_resolve_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{event_identifier}", None
    )
    assert media.url == f"/api/nest/event_media/{event_identifier}"
    assert media.mime_type == "video/mp4"

    # Fetch event media
    client = await hass_client()
    response = await client.get(media.url)
    assert response.status == HTTPStatus.OK, f"Response not matched: {response}"
    contents = await response.read()
    assert contents == IMAGE_BYTES_FROM_EVENT

    # Ensure event media store persists to disk
    await hass.async_block_till_done()

    # Unload the integration.
    assert config_entry.state is ConfigEntryState.LOADED
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED

    # Now rebuild the entire integration and verify that all persisted storage
    # can be re-loaded from disk.
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device
    assert device.name == DEVICE_NAME

    # Verify event metadata exists
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert len(browse.children) == 1
    assert browse.children[0].domain == DOMAIN
    event_timestamp_string = event_timestamp.strftime(DATE_STR_FORMAT)
    assert browse.children[0].title == f"Motion @ {event_timestamp_string}"
    assert not browse.children[0].can_expand
    assert browse.children[0].can_play
    event_identifier = browse.children[0].identifier

    media = await async_resolve_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{event_identifier}", None
    )
    assert media.url == f"/api/nest/event_media/{event_identifier}"
    assert media.mime_type == "video/mp4"

    # Verify media exists
    response = await client.get(media.url)
    assert response.status == HTTPStatus.OK, f"Response not matched: {response}"
    contents = await response.read()
    assert contents == IMAGE_BYTES_FROM_EVENT