def test_tracker_entity() -> None:
    """Test coverage for base TrackerEntity class."""
    entity = TrackerEntity()
    assert entity.source_type is SourceType.GPS
    assert entity.latitude is None
    assert entity.longitude is None
    assert entity.location_name is None
    assert entity.state is None
    assert entity.battery_level is None
    assert entity.should_poll is False
    assert entity.force_update is True
    assert entity.location_accuracy == 0

    class MockEntity(TrackerEntity):
        """Mock tracker class."""

        def __init__(self) -> None:
            """Initialize."""
            self.is_polling = False

        @property
        def should_poll(self) -> bool:
            """Return False for the test entity."""
            return self.is_polling

    test_entity = MockEntity()

    assert test_entity.force_update

    test_entity.is_polling = True

    assert not test_entity.force_update