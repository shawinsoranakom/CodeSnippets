def assert_valid_response_shape(result: dict, expected_template: int):
    """Assert that parser response has correct shape and types."""
    # Required keys
    assert "report" in result
    assert "template" in result
    assert "row_count" in result
    assert "data" in result

    # Type checks
    assert isinstance(result["report"], str)
    assert isinstance(result["template"], int)
    assert result["template"] == expected_template
    assert isinstance(result["row_count"], int)
    assert isinstance(result["data"], list)

    # row_count matches data length
    assert result["row_count"] == len(result["data"])

    # No error for valid input
    assert result.get("error") is None