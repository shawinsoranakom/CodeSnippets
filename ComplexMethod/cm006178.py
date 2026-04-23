async def test_openai_responses_rate_limiting_simulation(client: AsyncClient, created_api_key):
    """Test behavior under rapid successive requests."""
    flow, headers = await load_and_prepare_flow(client, created_api_key)

    # Send 10 rapid requests
    rapid_requests = []
    for i in range(10):
        payload = {"model": flow["id"], "input": f"Rapid request {i}", "stream": False}
        rapid_requests.append(client.post("/api/v1/responses", json=payload, headers=headers))

    # Wait for all requests to complete
    responses = await asyncio.gather(*rapid_requests, return_exceptions=True)

    # Check that most requests succeeded (allowing for some potential failures)
    successful_responses = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]

    # At least 50% should succeed
    assert len(successful_responses) >= 5

    # Check that successful responses have unique IDs
    response_ids = []
    for response in successful_responses:
        data = response.json()
        if "error" not in data or data["error"] is None:
            response_ids.append(data["id"])

    # All response IDs should be unique
    assert len(response_ids) == len(set(response_ids))