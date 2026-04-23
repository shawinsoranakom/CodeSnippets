def test_generate_response_from_error_with_valid_json() -> None:
    """Test `_generate_response_from_error` with valid JSON response."""
    response = MockResponse(
        status_code=400,
        headers={"content-type": "application/json"},
        json_data={"error": {"message": "Bad request", "type": "invalid_request"}},
    )
    error = MockAPIError("API Error", response=response)

    generations = _generate_response_from_error(error)

    assert len(generations) == 1
    generation = generations[0]
    assert isinstance(generation, ChatGeneration)
    assert isinstance(generation.message, AIMessage)
    assert generation.message.content == ""

    metadata = generation.message.response_metadata
    assert metadata["body"] == {
        "error": {"message": "Bad request", "type": "invalid_request"}
    }
    assert metadata["headers"] == {"content-type": "application/json"}
    assert metadata["status_code"] == 400