async def test_doorbell_fingerprint_identified_user_deactivated(
    hass: HomeAssistant,
    ufp: MockUFPFixture,
    doorbell: Camera,
    unadopted_camera: Camera,
    fixed_now: datetime,
) -> None:
    """Test a doorbell fingerprint identified event."""

    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.EVENT, 4, 4)
    events: list[HAEvent] = []

    @callback
    def _capture_event(event: HAEvent) -> None:
        events.append(event)

    _, entity_id = await ids_from_device_description(
        hass, Platform.EVENT, doorbell, EVENT_DESCRIPTIONS[2]
    )

    ulp_id = "ulp_id"
    test_user_full_name = "Test User"

    unsub = async_track_state_change_event(hass, entity_id, _capture_event)
    event = Event(
        model=ModelType.EVENT,
        id="test_event_id",
        type=EventType.FINGERPRINT_IDENTIFIED,
        start=fixed_now - timedelta(seconds=1),
        end=None,
        score=100,
        smart_detect_types=[],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
        metadata={"fingerprint": {"ulp_id": ulp_id}},
    )

    new_camera = doorbell.model_copy()
    new_camera.last_fingerprint_identified_event_id = "test_event_id"
    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_ulp_user = Mock()
    mock_ulp_user.ulp_id = ulp_id
    mock_ulp_user.full_name = test_user_full_name
    mock_ulp_user.status = "DEACTIVATED"
    ufp.api.bootstrap.ulp_users.add(mock_ulp_user)

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    assert len(events) == 1
    state = events[0].data["new_state"]
    assert state
    assert state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION
    assert state.attributes[ATTR_EVENT_ID] == "test_event_id"
    assert state.attributes["ulp_id"] == ulp_id
    assert state.attributes["full_name"] == "Test User"
    assert state.attributes["user_status"] == "DEACTIVATED"

    unsub()