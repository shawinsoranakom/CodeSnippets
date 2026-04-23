async def test_openai_responses_empty_input(client: AsyncClient, created_api_key):
    """Test the OpenAI responses endpoint with empty input."""
    flow, headers = await load_and_prepare_flow(client, created_api_key)

    # Test with empty input
    payload = {"model": flow["id"], "input": "", "stream": False}

    response = await client.post("/api/v1/responses", json=payload, headers=headers)
    logger.info(f"Empty input response status: {response.status_code}")

    # The flow might still process empty input, so we check for a valid response structure
    data = response.json()

    if "error" not in data or data["error"] is None:
        # Valid response even with empty input
        assert "id" in data
        assert "output" in data
        assert "created_at" in data
        assert data["object"] == "response"
    else:
        # Some flows might reject empty input
        assert isinstance(data["error"], dict)
        assert "message" in data["error"]