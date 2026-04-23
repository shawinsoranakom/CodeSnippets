async def test_openai_responses_stream_has_non_empty_content(client: AsyncClient, created_api_key):
    """Ensure streaming returns at least one chunk with non-empty delta.content."""
    flow, headers = await load_and_prepare_agent_flow(client, created_api_key)

    payload = {"model": flow["id"], "input": "Say something concise", "stream": True}
    response = await client.post("/api/v1/responses", json=payload, headers=headers)

    assert response.status_code == 200

    raw = await response.aread()
    text_content = raw.decode("utf-8")

    # Split SSE blocks and keep only data blocks
    blocks = [b for b in text_content.strip().split("\n\n") if b.startswith("data:")]
    has_non_empty = False
    for blk in blocks:
        data_part = blk.replace("data: ", "", 1).strip()
        if data_part == "[DONE]":
            continue
        try:
            obj = json.loads(data_part)
        except json.JSONDecodeError:
            # Not a JSON data block (could be our tool call events), skip
            continue
        if isinstance(obj, dict):
            delta = obj.get("delta")
            if isinstance(delta, dict):
                content = delta.get("content")
                if isinstance(content, str) and content.strip() != "":
                    has_non_empty = True
                    break

    assert has_non_empty, f"No non-empty content chunks found. First 300 chars: {text_content[:300]}"