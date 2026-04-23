async def test_multiple_devices(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    auth,
    hass_client: ClientSessionGenerator,
    create_device,
    subscriber,
    setup_platform,
) -> None:
    """Test events received for multiple devices."""
    device_id2 = f"{DEVICE_ID}-2"
    create_device.create(
        raw_data={
            "name": device_id2,
            "type": CAMERA_DEVICE_TYPE,
            "traits": CAMERA_TRAITS,
        }
    )
    await setup_platform()

    device1 = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device1
    device2 = device_registry.async_get_device(identifiers={(DOMAIN, device_id2)})
    assert device2

    # Very no events have been received yet
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")
    assert len(browse.children) == 2
    assert not browse.children[0].can_play
    assert not browse.children[1].can_play
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device1.id}")
    assert len(browse.children) == 0
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device2.id}")
    assert len(browse.children) == 0

    # Send events for device #1
    for i in range(5):
        auth.responses = [
            aiohttp.web.json_response(GENERATE_IMAGE_URL_RESPONSE),
            aiohttp.web.Response(body=IMAGE_BYTES_FROM_EVENT),
        ]
        await subscriber.async_receive_event(
            create_event(
                f"event-session-id-{i}",
                f"event-id-{i}",
                PERSON_EVENT,
                device_id=DEVICE_ID,
            )
        )
        await hass.async_block_till_done()

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")
    assert len(browse.children) == 2
    assert browse.children[0].can_play
    assert not browse.children[1].can_play
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device1.id}")
    assert len(browse.children) == 5
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device2.id}")
    assert len(browse.children) == 0

    # Send events for device #2
    for i in range(3):
        auth.responses = [
            aiohttp.web.json_response(GENERATE_IMAGE_URL_RESPONSE),
            aiohttp.web.Response(body=IMAGE_BYTES_FROM_EVENT),
        ]
        await subscriber.async_receive_event(
            create_event(
                f"other-id-{i}", f"event-id{i}", PERSON_EVENT, device_id=device_id2
            )
        )
        await hass.async_block_till_done()

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")
    assert len(browse.children) == 2
    assert browse.children[0].can_play
    assert browse.children[1].can_play
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device1.id}")
    assert len(browse.children) == 5
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device2.id}")
    assert len(browse.children) == 3