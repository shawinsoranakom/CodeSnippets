def test_scanner_entity() -> None:
    """Test coverage for base ScannerEntity entity class."""
    entity = ScannerEntity()
    assert entity.source_type is SourceType.ROUTER
    with pytest.raises(NotImplementedError):
        assert entity.is_connected is None
    with pytest.raises(NotImplementedError):
        assert entity.state == STATE_NOT_HOME
    assert entity.battery_level is None
    assert entity.ip_address is None
    assert entity.mac_address is None
    assert entity.hostname is None

    class MockEntity(ScannerEntity):
        """Mock scanner class."""

        def __init__(self) -> None:
            """Initialize."""
            self.mock_mac_address: str | None = None

        @property
        def mac_address(self) -> str | None:
            """Return the mac address of the device."""
            return self.mock_mac_address

    test_entity = MockEntity()

    assert test_entity.unique_id is None

    test_entity.mock_mac_address = TEST_MAC_ADDRESS

    assert test_entity.unique_id == TEST_MAC_ADDRESS