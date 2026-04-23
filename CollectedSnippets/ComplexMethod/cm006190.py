async def test_openai_streaming_success_finish_reason(client: AsyncClient, created_api_key, simple_api_test):
    """Test that successful streaming responses include finish_reason='stop'."""
    headers = {"x-api-key": created_api_key.api_key}
    payload = {
        "model": str(simple_api_test["id"]),
        "input": "Hello",
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
    finish_reason_stop = False

    for line in response.text.split("\n"):
        if line.startswith("data: ") and not line.startswith("data: [DONE]"):
            data_str = line[6:]
            try:
                chunk_data = json.loads(data_str)
                chunks.append(chunk_data)

                # Check for finish_reason="stop" in final chunk
                if chunk_data.get("finish_reason") == "stop":
                    finish_reason_stop = True

            except json.JSONDecodeError:
                pass

    # Verify that successful completion has finish_reason="stop"
    assert finish_reason_stop, "Successful completion should have finish_reason='stop'"
    assert len(chunks) > 0, "Should have received at least one chunk"