async def test_webhook_vertex_builds_contain_expected_data(client, added_webhook_test, created_api_key):
    """Test that vertex builds contain expected structure and data."""
    flow_id = added_webhook_test["id"]
    endpoint_name = added_webhook_test["endpoint_name"]
    endpoint = f"api/v1/webhook/{endpoint_name}"

    # Execute the webhook
    payload = {"verify": "structure"}
    response = await client.post(endpoint, headers={"x-api-key": created_api_key.api_key}, json=payload)
    assert response.status_code == 202

    # Wait for background task to complete
    await asyncio.sleep(2)

    # Check vertex builds
    builds_endpoint = f"api/v1/monitor/builds?flow_id={flow_id}"
    builds_response = await client.get(builds_endpoint, headers={"x-api-key": created_api_key.api_key})

    assert builds_response.status_code == 200
    builds_data = builds_response.json()

    # Verify structure of vertex builds
    for builds in builds_data["vertex_builds"].values():
        assert isinstance(builds, list)
        for build in builds:
            assert "id" in build
            assert "valid" in build
            assert "timestamp" in build
            assert "flow_id" in build
            assert str(build["flow_id"]) == flow_id