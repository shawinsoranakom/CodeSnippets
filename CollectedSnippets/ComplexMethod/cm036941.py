async def test_chat_completion_render_with_stream_true(client):
    """Render accepts stream params but still returns JSON (non-streamed)."""

    response = await client.post(
        "/v1/chat/completions/render",
        json={
            "model": MODEL_NAME,
            "stream": True,
            "stream_options": {
                "include_usage": True,
                "continuous_usage_stats": True,
            },
            "messages": [
                {
                    "role": "user",
                    "content": "Stream options should be accepted by /render.",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/json")

    data = response.json()
    assert isinstance(data, dict)
    assert "token_ids" in data
    assert isinstance(data["token_ids"], list)
    assert len(data["token_ids"]) > 0

    # /render should preserve stream fields on the returned token-in request.
    assert data.get("stream") is True
    assert isinstance(data.get("stream_options"), dict)
    assert data["stream_options"].get("include_usage") is True
    assert data["stream_options"].get("continuous_usage_stats") is True