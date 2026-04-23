def test_result_data_response_nested_structures(long_list, long_dict):
    """Test that ResultDataResponse handles nested structures correctly."""
    nested_data = {
        "list": long_list,
        "dict": long_dict,
    }

    ResultDataResponse(results=nested_data)
    serialized = serialize(nested_data, max_length=TEST_TEXT_LENGTH)

    # Check list items
    for item in serialized["list"]:
        assert len(item) <= TEST_TEXT_LENGTH + len("...")
        if len(item) > TEST_TEXT_LENGTH:
            assert "..." in item

    # Check dict values
    for val in serialized["dict"].values():
        assert len(val) <= TEST_TEXT_LENGTH + len("...")
        if len(val) > TEST_TEXT_LENGTH:
            assert "..." in val