async def test_event() -> None:
    """Test the event entity."""
    event = EventEntity()
    event.entity_id = "event.doorbell"
    # Test event with no data at all
    assert event.state is None
    assert event.state_attributes == {ATTR_EVENT_TYPE: None}
    assert not event.extra_state_attributes
    assert event.device_class is None

    # No event types defined, should raise
    with pytest.raises(AttributeError):
        _ = event.event_types

    # Test retrieving data from entity description
    event.entity_description = EventEntityDescription(
        key="test_event",
        event_types=["short_press", "long_press"],
        device_class=EventDeviceClass.DOORBELL,
    )
    # Delete the cache since we changed the entity description
    # at run time
    del event.device_class
    assert event.event_types == ["short_press", "long_press"]
    assert event.device_class == EventDeviceClass.DOORBELL

    # Test attrs win over entity description
    event._attr_event_types = ["short_press", "long_press", "double_press"]
    assert event.event_types == ["short_press", "long_press", "double_press"]
    event._attr_device_class = EventDeviceClass.BUTTON
    assert event.device_class == EventDeviceClass.BUTTON

    # Test triggering an event
    now = dt_util.utcnow()
    with freeze_time(now):
        event._trigger_event("long_press")

        assert event.state == now.isoformat(timespec="milliseconds")
        assert event.state_attributes == {ATTR_EVENT_TYPE: "long_press"}
        assert not event.extra_state_attributes

    # Test triggering an event, with extra attribute data
    now = dt_util.utcnow()
    with freeze_time(now):
        event._trigger_event("short_press", {"hello": "world"})

        assert event.state == now.isoformat(timespec="milliseconds")
        assert event.state_attributes == {
            ATTR_EVENT_TYPE: "short_press",
            "hello": "world",
        }

    # Test triggering an unknown event
    with pytest.raises(
        ValueError, match="^Invalid event type unknown_event for event.doorbell$"
    ):
        event._trigger_event("unknown_event")