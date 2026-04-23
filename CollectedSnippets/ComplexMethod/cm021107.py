async def test_binary_sensor_simultaneous_person_and_vehicle_detection(
    hass: HomeAssistant,
    ufp: MockUFPFixture,
    doorbell: Camera,
    unadopted_camera: Camera,
    fixed_now: datetime,
) -> None:
    """Test that when an event is updated with additional detection types, both trigger.

    This is a regression test for https://github.com/home-assistant/core/issues/152133
    where an event starting with vehicle detection gets updated to also include person
    detection (e.g., someone getting out of a car). Both sensors should be ON
    simultaneously, not queued.
    """

    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 15, 15)

    doorbell.smart_detect_settings.object_types.append(SmartDetectObjectType.PERSON)
    doorbell.smart_detect_settings.object_types.append(SmartDetectObjectType.VEHICLE)

    # Get entity IDs for both person and vehicle detection
    _, person_entity_id = await ids_from_device_description(
        hass,
        Platform.BINARY_SENSOR,
        doorbell,
        EVENT_SENSORS[3],  # person detected
    )
    _, vehicle_entity_id = await ids_from_device_description(
        hass,
        Platform.BINARY_SENSOR,
        doorbell,
        EVENT_SENSORS[4],  # vehicle detected
    )

    # Step 1: Initial event with only VEHICLE detection (car arriving)
    event = Event(
        model=ModelType.EVENT,
        id="combined_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=5),
        end=None,  # Event is ongoing
        score=90,
        smart_detect_types=[SmartDetectObjectType.VEHICLE],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.VEHICLE] = event.id

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    # Vehicle sensor should be ON
    vehicle_state = hass.states.get(vehicle_entity_id)
    assert vehicle_state
    assert vehicle_state.state == STATE_ON, "Vehicle detection should be ON"

    # Person sensor should still be OFF (no person detected yet)
    person_state = hass.states.get(person_entity_id)
    assert person_state
    assert person_state.state == STATE_OFF, "Person detection should be OFF initially"

    # Step 2: Same event gets updated to include PERSON detection
    # (someone gets out of the car - Protect adds PERSON to the same event)
    #
    # BUG SCENARIO: UniFi Protect updates the event to include PERSON in
    # smart_detect_types, BUT does NOT update last_smart_detect_event_ids[PERSON]
    # until the event ends. This is the core issue reported in #152133.
    updated_event = Event(
        model=ModelType.EVENT,
        id="combined_event_id",  # Same event ID!
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=5),
        end=None,  # Event still ongoing
        score=90,
        smart_detect_types=[
            SmartDetectObjectType.VEHICLE,
            SmartDetectObjectType.PERSON,
        ],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    # IMPORTANT: The camera's last_smart_detect_event_ids is NOT updated for PERSON!
    # This simulates the real bug where UniFi Protect doesn't immediately update
    # the camera's last_smart_detect_event_ids when a new detection type is added
    # to an ongoing event.
    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    # Only VEHICLE has the event ID - PERSON does not (simulating the bug)
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.VEHICLE] = (
        updated_event.id
    )
    # NOTE: We're NOT setting last_smart_detect_event_ids[PERSON] to simulate the bug!

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {updated_event.id: updated_event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = updated_event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    # CRITICAL: Both sensors should now be ON simultaneously
    vehicle_state = hass.states.get(vehicle_entity_id)
    assert vehicle_state
    assert vehicle_state.state == STATE_ON, (
        "Vehicle detection should still be ON after event update"
    )

    person_state = hass.states.get(person_entity_id)
    assert person_state
    assert person_state.state == STATE_ON, (
        "Person detection should be ON immediately when added to event, "
        "not waiting for vehicle detection to end"
    )

    # Verify both have correct attributes
    assert vehicle_state.attributes[ATTR_EVENT_SCORE] == 90
    assert person_state.attributes[ATTR_EVENT_SCORE] == 90

    # Step 3: Event ends - both sensors should turn OFF
    ended_event = Event(
        model=ModelType.EVENT,
        id="combined_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=5),
        end=fixed_now,  # Event ended now
        score=90,
        smart_detect_types=[
            SmartDetectObjectType.VEHICLE,
            SmartDetectObjectType.PERSON,
        ],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    ufp.api.bootstrap.events = {ended_event.id: ended_event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = ended_event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    # Both should be OFF now
    vehicle_state = hass.states.get(vehicle_entity_id)
    assert vehicle_state
    assert vehicle_state.state == STATE_OFF, (
        "Vehicle detection should be OFF after event ends"
    )

    person_state = hass.states.get(person_entity_id)
    assert person_state
    assert person_state.state == STATE_OFF, (
        "Person detection should be OFF after event ends"
    )