async def test_vehicle_detection_new_event_cancels_timer(
    hass: HomeAssistant,
    ufp: MockUFPFixture,
    doorbell: Camera,
    unadopted_camera: Camera,
    fixed_now: datetime,
) -> None:
    """Test that new event cancels timer for previous event."""

    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.EVENT, 4, 4)
    events: list[HAEvent] = []

    @callback
    def _capture_event(event: HAEvent) -> None:
        events.append(event)

    _, entity_id = await ids_from_device_description(
        hass, Platform.EVENT, doorbell, EVENT_DESCRIPTIONS[3]
    )

    unsub = async_track_state_change_event(hass, entity_id, _capture_event)

    # Create first event
    event1 = Event(
        model=ModelType.EVENT,
        id="test_event_1",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=5),
        end=None,
        score=100,
        smart_detect_types=[],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
        metadata={
            "detected_thumbnails": [
                {
                    "type": "vehicle",
                    "confidence": 80,
                    "clock_best_wall": fixed_now - timedelta(seconds=4),
                    "cropped_id": "test_thumb_id",
                    "group": {
                        "id": "lpr_group_5",
                        "matched_name": "FIRST",
                        "confidence": 80,
                    },
                }
            ]
        },
    )

    new_camera = doorbell.model_copy()
    new_camera.last_smart_detect_event_id = "test_event_1"
    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event1.id: event1}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event1
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    # Wait briefly (timer hasn't expired yet)
    await asyncio.sleep(TEST_VEHICLE_EVENT_DELAY / 2)
    await hass.async_block_till_done()

    # No event yet
    assert len(events) == 0

    # Send new event - should fire first event immediately
    event2 = Event(
        model=ModelType.EVENT,
        id="test_event_2",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=1),
        end=None,
        score=100,
        smart_detect_types=[],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
        metadata={
            "detected_thumbnails": [
                {
                    "type": "vehicle",
                    "confidence": 95,
                    "clock_best_wall": fixed_now,
                    "cropped_id": "test_thumb_id",
                    "group": {
                        "id": "lpr_group_6",
                        "matched_name": "SECOND",
                        "confidence": 95,
                    },
                }
            ]
        },
    )

    new_camera.last_smart_detect_event_id = "test_event_2"
    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event2.id: event2}

    mock_msg.new_obj = event2
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    # Wait for second event's timer
    await asyncio.sleep(TEST_VEHICLE_EVENT_DELAY * 2)
    await hass.async_block_till_done()

    # Should have two events - first fired immediately when second arrived
    assert len(events) == 2
    # First event fired immediately when second event arrived
    state = events[0].data["new_state"]
    assert state
    assert state.attributes[ATTR_EVENT_ID] == "test_event_1"
    assert state.attributes["license_plate"] == "FIRST"
    # Second event fired after timer
    state = events[1].data["new_state"]
    assert state
    assert state.attributes[ATTR_EVENT_ID] == "test_event_2"
    assert state.attributes["license_plate"] == "SECOND"

    unsub()