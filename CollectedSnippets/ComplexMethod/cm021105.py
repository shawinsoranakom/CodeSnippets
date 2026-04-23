async def test_binary_sensor_package_detected(
    hass: HomeAssistant,
    ufp: MockUFPFixture,
    doorbell: Camera,
    unadopted_camera: Camera,
    fixed_now: datetime,
) -> None:
    """Test binary_sensor package detection entity."""

    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 15, 15)

    doorbell.smart_detect_settings.object_types.append(SmartDetectObjectType.PACKAGE)

    _, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, doorbell, EVENT_SENSORS[6]
    )

    event = Event(
        model=ModelType.EVENT,
        id="test_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=1),
        end=None,
        score=100,
        smart_detect_types=[SmartDetectObjectType.PACKAGE],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.PACKAGE] = event.id

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION
    assert state.attributes[ATTR_EVENT_SCORE] == 100

    event = Event(
        model=ModelType.EVENT,
        id="test_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=1),
        end=fixed_now + timedelta(seconds=1),
        score=50,
        smart_detect_types=[SmartDetectObjectType.PACKAGE],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.PACKAGE] = event.id

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    # Event is already seen and has end, should now be off
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    # Now send an event that has an end right away
    event = Event(
        model=ModelType.EVENT,
        id="new_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=1),
        end=fixed_now + timedelta(seconds=1),
        score=80,
        smart_detect_types=[SmartDetectObjectType.PACKAGE],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.PACKAGE] = event.id

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event

    state_changes: list[HAEvent[EventStateChangedData]] = async_capture_events(
        hass, EVENT_STATE_CHANGED
    )
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    assert len(state_changes) == 2

    on_event = state_changes[0]
    state = on_event.data["new_state"]
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION
    assert state.attributes[ATTR_EVENT_SCORE] == 80

    off_event = state_changes[1]
    state = off_event.data["new_state"]
    assert state
    assert state.state == STATE_OFF
    assert ATTR_EVENT_SCORE not in state.attributes

    # replay and ensure ignored
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()
    assert len(state_changes) == 2