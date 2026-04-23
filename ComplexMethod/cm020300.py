async def test_event(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    auth,
    setup_platform,
    subscriber,
    event_trait,
    expected_model,
    expected_type,
) -> None:
    """Test a pubsub message for a doorbell event."""
    events = async_capture_events(hass, NEST_EVENT)
    await setup_platform()

    entry = entity_registry.async_get("camera.front")
    assert entry is not None
    assert entry.unique_id == f"{DEVICE_ID}-camera"
    assert entry.domain == "camera"

    device = device_registry.async_get(entry.device_id)
    assert device.name == "Front"
    assert device.model == expected_model
    assert device.identifiers == {("nest", DEVICE_ID)}

    auth.responses = [
        aiohttp.web.json_response(GENERATE_IMAGE_URL_RESPONSE),
        aiohttp.web.Response(body=IMAGE_BYTES_FROM_EVENT),
    ]

    timestamp = utcnow()
    await subscriber.async_receive_event(create_event(event_trait, timestamp=timestamp))
    await hass.async_block_till_done()

    event_time = timestamp.replace(microsecond=0)
    assert len(events) == 1
    assert event_view(events[0].data) == {
        "device_id": entry.device_id,
        "type": expected_type,
        "timestamp": event_time,
    }
    assert "image" in events[0].data["attachment"]
    assert "video" not in events[0].data["attachment"]