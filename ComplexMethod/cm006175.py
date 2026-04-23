async def test_openai_responses_response_format(client: AsyncClient, created_api_key):
    """Test OpenAI response format compliance."""
    flow, headers = await load_and_prepare_flow(client, created_api_key)

    payload = {"model": flow["id"], "input": "Hello", "stream": False}
    response = await client.post("/api/v1/responses", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()

    if "error" not in data or data["error"] is None:
        # Check OpenAI response format compliance
        required_fields = ["id", "object", "created_at", "status", "model", "output"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check field types and values
        assert isinstance(data["id"], str)
        assert data["object"] == "response"
        assert isinstance(data["created_at"], int)
        assert data["status"] in ["completed", "in_progress", "failed"]
        assert isinstance(data["model"], str)
        assert isinstance(data["output"], list)

        # Check optional fields with expected defaults
        assert data["parallel_tool_calls"] is True
        assert data["store"] is True
        assert data["temperature"] == 1.0
        assert data["top_p"] == 1.0
        assert data["truncation"] == "disabled"
        assert data["tool_choice"] == "auto"
        assert isinstance(data["tools"], list)
        assert isinstance(data["reasoning"], dict)
        assert isinstance(data["text"], dict)
        assert isinstance(data["metadata"], dict)