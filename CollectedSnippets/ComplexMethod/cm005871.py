def test_split_truncates_oversized_field_in_multi_field_payload():
    """Test that oversized field gets truncated when splitting multi-field payload."""
    # Create inputs with normal fields and one oversized field
    inputs = {
        "normal1": "value1",
        "normal2": "value2",
        "huge_field": "x" * 5000,
        "normal3": "value3",
    }

    payload = ComponentInputsPayload(
        component_run_id="test-run-id",
        component_id="test-comp-id",
        component_name="TestComponent",
        component_inputs=inputs,
    )

    result = payload.split_if_needed(max_url_size=MAX_TELEMETRY_URL_SIZE)

    # Should be split into multiple chunks
    assert len(result) > 1

    # All chunks must respect max size
    for chunk in result:
        chunk_size = chunk._calculate_url_size()
        assert chunk_size <= MAX_TELEMETRY_URL_SIZE

    # The huge_field should be truncated
    huge_field_found = False
    for chunk in result:
        if "huge_field" in chunk.component_inputs:
            huge_field_found = True
            assert "...[truncated]" in chunk.component_inputs["huge_field"]
            assert len(chunk.component_inputs["huge_field"]) < 5000

    assert huge_field_found, "huge_field should be in one of the chunks"