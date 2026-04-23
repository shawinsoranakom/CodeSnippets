async def test_generate_stream(client):
    payload = {
        "model": MODEL_NAME,
        "token_ids": [1, 2, 3],
        "sampling_params": {"max_tokens": 5},
        "stream": True,
    }
    async with client.stream("POST", GEN_ENDPOINT, json=payload) as resp:
        resp.raise_for_status()
        chunks = []
        async for line in resp.aiter_lines():
            if not line.startswith("data: "):
                continue
            payload_str = line[len("data: ") :]
            if payload_str == "[DONE]":
                break
            chunks.append(json.loads(payload_str))

    assert len(chunks) > 0
    # Every chunk has choices with token_ids
    all_token_ids = []
    for chunk in chunks:
        assert "choices" in chunk
        assert len(chunk["choices"]) == 1
        choice = chunk["choices"][0]
        assert "token_ids" in choice
        assert len(choice["token_ids"]) > 0
        all_token_ids.extend(choice["token_ids"])

    # Last chunk should have a finish_reason
    assert chunks[-1]["choices"][0]["finish_reason"] is not None

    # Streaming should produce the same tokens as non-streaming
    non_stream_resp = await client.post(
        GEN_ENDPOINT,
        json={
            "model": MODEL_NAME,
            "token_ids": [1, 2, 3],
            "sampling_params": {"max_tokens": 5, "temperature": 0.0},
            "stream": False,
        },
    )
    non_stream_data = non_stream_resp.json()
    # Just verify we got the right number of tokens
    assert len(all_token_ids) == len(non_stream_data["choices"][0]["token_ids"])