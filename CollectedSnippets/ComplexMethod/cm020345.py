async def test_event_threads(
    hass: HomeAssistant,
    subscriber: AsyncMock,
    setup_platform: PlatformSetup,
    create_device: CreateDevice,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test multiple events delivered as part of a thread are a single home assistant event."""
    create_device.create(
        raw_traits={
            TraitType.DOORBELL_CHIME: {},
            TraitType.CAMERA_CLIP_PREVIEW: {},
        }
    )
    await setup_platform()

    state = hass.states.get("event.front_chime")
    assert state.state == "unknown"

    # Doorbell event is received
    freezer.tick(datetime.timedelta(seconds=2))
    await subscriber.async_receive_event(
        create_event_messages(
            {
                EventType.DOORBELL_CHIME: {
                    "eventSessionId": EVENT_SESSION_ID,
                    "eventId": EVENT_ID,
                }
            },
            parameters={"eventThreadState": "STARTED"},
        )
    )
    await hass.async_block_till_done()

    state = hass.states.get("event.front_chime")
    assert state.state == "2024-08-24T12:00:02.000+00:00"
    assert state.attributes == {
        "device_class": "doorbell",
        "event_types": ["doorbell_chime"],
        "friendly_name": "Front Chime",
        "event_type": "doorbell_chime",
        "nest_event_id": ENCODED_EVENT_ID,
    }

    # Media arrives in a second message that ends the thread
    freezer.tick(datetime.timedelta(seconds=2))
    await subscriber.async_receive_event(
        create_event_messages(
            {
                EventType.DOORBELL_CHIME: {
                    "eventSessionId": EVENT_SESSION_ID,
                    "eventId": EVENT_ID,
                },
                EventType.CAMERA_CLIP_PREVIEW: {
                    "eventSessionId": EVENT_SESSION_ID,
                    "previewUrl": TEST_CLIP_URL,
                },
            },
            parameters={"eventThreadState": "ENDED"},
        )
    )
    await hass.async_block_till_done()

    state = hass.states.get("event.front_chime")
    assert (
        state.state == "2024-08-24T12:00:02.000+00:00"
    )  # A second event is not received
    assert state.attributes == {
        "device_class": "doorbell",
        "event_types": ["doorbell_chime"],
        "friendly_name": "Front Chime",
        "event_type": "doorbell_chime",
        "nest_event_id": ENCODED_EVENT_ID,
    }

    # An additional doorbell press event happens (with an updated session id)
    freezer.tick(datetime.timedelta(seconds=2))
    await subscriber.async_receive_event(
        create_event_messages(
            {
                EventType.DOORBELL_CHIME: {
                    "eventSessionId": EVENT_SESSION_ID2,
                    "eventId": EVENT_ID2,
                },
                EventType.CAMERA_CLIP_PREVIEW: {
                    "eventSessionId": EVENT_SESSION_ID2,
                    "previewUrl": TEST_CLIP_URL,
                },
            },
            parameters={"eventThreadState": "ENDED"},
        )
    )
    await hass.async_block_till_done()

    state = hass.states.get("event.front_chime")
    assert state.state == "2024-08-24T12:00:06.000+00:00"  # Third event is received
    assert state.attributes == {
        "device_class": "doorbell",
        "event_types": ["doorbell_chime"],
        "friendly_name": "Front Chime",
        "event_type": "doorbell_chime",
        "nest_event_id": ENCODED_EVENT_ID2,
    }