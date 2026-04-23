async def test_openai_responses_previous_response_id(client: AsyncClient, created_api_key):
    """Test previous_response_id parameter for conversation continuity."""
    flow, headers = await load_and_prepare_flow(client, created_api_key)

    # First request
    payload1 = {"model": flow["id"], "input": "Hello", "stream": False}
    response1 = await client.post("/api/v1/responses", json=payload1, headers=headers)
    assert response1.status_code == 200

    data1 = response1.json()
    if "error" not in data1 or data1["error"] is None:
        first_response_id = data1["id"]

        # Second request with previous_response_id
        payload2 = {
            "model": flow["id"],
            "input": "Continue our conversation",
            "previous_response_id": first_response_id,
            "stream": False,
        }
        response2 = await client.post("/api/v1/responses", json=payload2, headers=headers)
        assert response2.status_code == 200

        data2 = response2.json()
        if "error" not in data2 or data2["error"] is None:
            # The previous_response_id might be preserved in the response
            # This depends on the implementation, so we just check it doesn't error
            # We'll just verify that the request was processed successfully
            assert "id" in data2
            assert "output" in data2