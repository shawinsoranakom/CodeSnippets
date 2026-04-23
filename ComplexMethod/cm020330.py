async def test_remove_stale_media(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    auth,
    mp4,
    hass_client: ClientSessionGenerator,
    subscriber,
    setup_platform,
    media_path: str,
) -> None:
    """Test media files getting evicted from the cache."""
    await setup_platform()

    device = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device
    assert device.name == DEVICE_NAME

    # Publish a media event
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

    # The first subdirectory is the device id. Media for events are stored in the
    # device subdirectory. First verify that the media was persisted. We will
    # then add additional media files, then invoke the garbage collector, and
    # then verify orphaned files are removed.
    storage_path = pathlib.Path(media_path)
    device_path = storage_path / device.id
    media_files = list(device_path.glob("*"))
    assert len(media_files) == 1
    event_media = media_files[0]
    assert event_media.name.endswith(".mp4")

    event_time1 = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=8)
    extra_media1 = (
        device_path / f"{int(event_time1.timestamp())}-camera_motion-test.mp4"
    )
    extra_media1.write_bytes(mp4.getvalue())
    event_time2 = event_time1 + datetime.timedelta(hours=20)
    extra_media2 = (
        device_path / f"{int(event_time2.timestamp())}-camera_motion-test.jpg"
    )
    extra_media2.write_bytes(mp4.getvalue())
    # This event will not be garbage collected because it is too recent
    event_time3 = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=3)
    extra_media3 = (
        device_path / f"{int(event_time3.timestamp())}-camera_motion-test.mp4"
    )
    extra_media3.write_bytes(mp4.getvalue())

    assert len(list(device_path.glob("*"))) == 4

    # Advance the clock to invoke the garbage collector. This will remove extra
    # files that are not valid events that are old enough.
    point_in_time = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
    with freeze_time(point_in_time):
        async_fire_time_changed(hass, point_in_time)
        await hass.async_block_till_done()
        await hass.async_block_till_done()

    # Verify that the event media is still present and that the extra files
    # are removed. Newer media is not removed.
    assert event_media.exists()
    assert not extra_media1.exists()
    assert not extra_media2.exists()
    assert extra_media3.exists()