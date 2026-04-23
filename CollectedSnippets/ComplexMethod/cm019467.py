def test_entity_entry_as_dict() -> None:
    """Test entity_entry_as_dict."""
    created = datetime.fromisoformat("2024-01-01T00:00:00+00:00")
    entry = RegistryEntry(
        entity_id="sensor.test_sensor",
        unique_id="unique123",
        platform="test",
        capabilities=None,
        config_entry_id=None,
        config_subentry_id=None,
        created_at=created,
        device_id=None,
        disabled_by=None,
        entity_category=None,
        has_entity_name=False,
        hidden_by=None,
        id=None,
        options=None,
        original_device_class=None,
        original_icon=None,
        original_name="Test Sensor",
        object_id_base=None,
        suggested_object_id=None,
        supported_features=0,
        translation_key=None,
        unit_of_measurement=None,
    )

    result = entity_entry_as_dict(entry)

    assert isinstance(result, dict)
    assert "_cache" not in result
    assert result["entity_id"] == "sensor.test_sensor"
    assert result["unique_id"] == "unique123"
    assert result["platform"] == "test"
    assert result["original_name"] == "Test Sensor"
    assert result["supported_features"] == 0
    assert result["created_at"] == created