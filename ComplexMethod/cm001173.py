def assert_error_response_structure(
    response: Any,
    expected_status: int = 422,
    expected_error_fields: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Assert error response has expected structure.

    Args:
        response: The HTTP response object
        expected_status: Expected error status code
        expected_error_fields: List of expected fields in error detail

    Returns:
        Parsed error response
    """
    assert_response_status(response, expected_status, "Error response check")

    error_data = safe_parse_json(response, "Error response parsing")

    # Check basic error structure
    assert "detail" in error_data, f"Missing 'detail' in error response: {error_data}"

    # Check specific error fields if provided
    if expected_error_fields:
        detail = error_data["detail"]
        if isinstance(detail, list):
            # FastAPI validation errors
            for error in detail:
                assert "loc" in error, f"Missing 'loc' in error: {error}"
                assert "msg" in error, f"Missing 'msg' in error: {error}"
                assert "type" in error, f"Missing 'type' in error: {error}"

    return error_data