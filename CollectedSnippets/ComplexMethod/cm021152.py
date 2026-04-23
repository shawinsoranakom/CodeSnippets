async def test_vehicle_detection_refire_on_lpr_data(
    hass: HomeAssistant,
    ufp: MockUFPFixture,
    doorbell: Camera,
    unadopted_camera: Camera,
    fixed_now: datetime,
) -> None:
    """Test that event refires when LPR data arrives after initial detection."""

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

    # Create event with vehicle thumbnail but NO LPR data
    event = Event(
        model=ModelType.EVENT,
        id="test_refire_lpr_id",
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
                    "confidence": 85,
                    "clock_best_wall": fixed_now,
                    "cropped_id": "test_thumb_id",
                }
            ]
        },
    )

    new_camera = doorbell.model_copy()
    new_camera.last_smart_detect_event_id = "test_refire_lpr_id"
    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    # Wait for the timer to expire - first event should fire without LPR
    await asyncio.sleep(TEST_VEHICLE_EVENT_DELAY * 2)
    await hass.async_block_till_done()

    # Should have received first event without LPR
    assert len(events) == 1
    state = events[0].data["new_state"]
    assert state
    assert state.attributes[ATTR_EVENT_ID] == "test_refire_lpr_id"
    assert state.attributes["confidence"] == 85
    assert "license_plate" not in state.attributes

    # Now LPR data arrives for the same event
    event.metadata = {
        "detected_thumbnails": [
            {
                "type": "vehicle",
                "confidence": 85,
                "clock_best_wall": fixed_now,
                "cropped_id": "test_thumb_id",
            },
            {
                "type": "vehicle",
                "confidence": 95,
                "clock_best_wall": fixed_now + timedelta(seconds=1),
                "cropped_id": "test_thumb_id_lpr",
                "group": {
                    "id": "lpr_group",
                    "matched_name": "ABC123",
                    "confidence": 95,
                },
            },
        ]
    }

    ufp.api.bootstrap.events = {event.id: event}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    # Wait for the new timer to expire
    await asyncio.sleep(TEST_VEHICLE_EVENT_DELAY * 2)
    await hass.async_block_till_done()

    # Should have received second event WITH LPR data
    assert len(events) == 2
    state = events[1].data["new_state"]
    assert state
    assert state.attributes[ATTR_EVENT_ID] == "test_refire_lpr_id"
    assert state.attributes["confidence"] == 95
    assert state.attributes["license_plate"] == "ABC123"

    unsub()