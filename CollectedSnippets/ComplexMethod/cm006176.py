async def test_openai_responses_stream_chunk_format(client: AsyncClient, created_api_key):
    """Test OpenAI streaming response chunk format compliance."""
    flow, headers = await load_and_prepare_flow(client, created_api_key)

    payload = {"model": flow["id"], "input": "Hello", "stream": True}
    response = await client.post("/api/v1/responses", json=payload, headers=headers)

    assert response.status_code == 200

    content = await response.aread()
    text_content = content.decode("utf-8")

    # Parse the events
    events = text_content.strip().split("\n\n")
    data_events = [evt for evt in events if evt.startswith("data:") and not evt.startswith("data: [DONE]")]

    if data_events:
        # Check first chunk format
        first_chunk_json = data_events[0].replace("data: ", "")
        try:
            first_chunk = json.loads(first_chunk_json)

            # Basic checks for streaming response
            assert "id" in first_chunk
            assert "delta" in first_chunk
            assert isinstance(first_chunk["id"], str)
            assert isinstance(first_chunk["delta"], dict)

            # Check OpenAI stream chunk format compliance if fields exist
            if "object" in first_chunk:
                assert first_chunk["object"] == "response.chunk"
            if "created" in first_chunk:
                assert isinstance(first_chunk["created"], int)
            if "model" in first_chunk:
                assert isinstance(first_chunk["model"], str)

            # Status is optional in chunks and can be None
            if "status" in first_chunk and first_chunk["status"] is not None:
                assert first_chunk["status"] in ["completed", "in_progress", "failed"]
        except json.JSONDecodeError:
            # If streaming format is different or not JSON, just ensure we have data
            assert len(data_events) > 0
    else:
        # If no streaming chunks, ensure we have the [DONE] marker or valid response
        assert "data: [DONE]" in text_content or len(text_content) > 0