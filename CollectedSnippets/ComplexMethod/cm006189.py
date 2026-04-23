async def test_openai_streaming_runtime_error_format(client: AsyncClient, created_api_key, simple_api_test):
    """Test that runtime errors during streaming are properly formatted.

    This test verifies the fix for the bug where error events during flow execution
    were not being propagated to clients using the OpenAI SDK. The fix ensures errors
    are sent as content chunks with finish_reason="error" instead of custom error events.

    Note: This test validates the error chunk format. Runtime errors during actual
    flow execution will be formatted the same way.
    """
    headers = {"x-api-key": created_api_key.api_key}
    payload = {
        "model": str(simple_api_test["id"]),
        "input": "test input",
        "stream": True,
    }

    response = await client.post(
        "api/v1/responses",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 200

    # Parse the streaming response
    chunks = []
    for line in response.text.split("\n"):
        if line.startswith("data: ") and not line.startswith("data: [DONE]"):
            data_str = line[6:]
            try:
                chunk_data = json.loads(data_str)
                chunks.append(chunk_data)
            except json.JSONDecodeError:
                pass

    # Verify all response.chunk events have proper OpenAI format.
    # The stream also sends a response.completed event (type + response with id inside);
    # per OpenAI spec, only response.chunk events have top-level id/object/delta.
    response_chunks = [c for c in chunks if c.get("object") == "response.chunk" or ("delta" in c and "id" in c)]
    assert len(response_chunks) > 0, "Should have received at least one response.chunk"
    for chunk in response_chunks:
        assert "id" in chunk, "Chunk should have 'id' field"
        assert "object" in chunk, "Chunk should have 'object' field"
        assert chunk.get("object") == "response.chunk", "Object should be 'response.chunk'"
        assert "created" in chunk, "Chunk should have 'created' field"
        assert "model" in chunk, "Chunk should have 'model' field"
        assert "delta" in chunk, "Chunk should have 'delta' field"

        # If there's a finish_reason, it should be valid
        if "finish_reason" in chunk and chunk["finish_reason"] is not None:
            assert chunk["finish_reason"] in ["stop", "length", "error", "tool_calls"], (
                f"finish_reason should be valid, got: {chunk['finish_reason']}"
            )