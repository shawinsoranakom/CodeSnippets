def test_sensor_truncation_logic() -> None:
    """Test sensor truncation logic for body sensor."""
    provider = _create_mock_provider()
    sensor = _create_test_sensor(provider, "body")

    # Test long body truncation
    long_body = "a" * (MAX_LENGTH_STATE_STATE + 50)
    provider.data = {
        "body": long_body,
        "title": "Test Title",
        "type": "note",
    }

    sensor.async_update_callback()

    # Verify truncation
    assert len(sensor._attr_native_value) == MAX_LENGTH_STATE_STATE
    assert sensor._attr_native_value.endswith("...")
    assert sensor._attr_native_value.startswith("a")
    assert sensor._attr_extra_state_attributes["body"] == long_body

    # Test normal length body
    normal_body = "This is a normal body"
    provider.data = {
        "body": normal_body,
        "title": "Test Title",
        "type": "note",
    }

    sensor.async_update_callback()

    # Verify no truncation
    assert sensor._attr_native_value == normal_body
    assert len(sensor._attr_native_value) < MAX_LENGTH_STATE_STATE
    assert sensor._attr_extra_state_attributes["body"] == normal_body

    # Test exactly max length
    exact_body = "a" * MAX_LENGTH_STATE_STATE
    provider.data = {
        "body": exact_body,
        "title": "Test Title",
        "type": "note",
    }

    sensor.async_update_callback()

    # Verify no truncation at the limit
    assert sensor._attr_native_value == exact_body
    assert len(sensor._attr_native_value) == MAX_LENGTH_STATE_STATE
    assert sensor._attr_extra_state_attributes["body"] == exact_body