async def test_openai_responses_concurrent_requests(client: AsyncClient, created_api_key):
    """Test handling of concurrent requests to the same flow."""
    flow, headers = await load_and_prepare_flow(client, created_api_key)

    # Create multiple concurrent requests
    payloads = [{"model": flow["id"], "input": f"Request {i}", "stream": False} for i in range(5)]

    # Send all requests concurrently
    tasks = [client.post("/api/v1/responses", json=payload, headers=headers) for payload in payloads]

    responses = await asyncio.gather(*tasks)

    # All requests should succeed
    for i, response in enumerate(responses):
        assert response.status_code == 200
        data = response.json()

        if "error" not in data:
            assert "id" in data
            assert "output" in data
            # Each response should have a unique ID
            assert all(
                data["id"] != other.json()["id"]
                for j, other in enumerate(responses)
                if i != j and "error" not in other.json()
            )