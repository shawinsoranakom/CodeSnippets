async def test_sync_execution_response_structure_validation(
        self,
        client: AsyncClient,
        created_api_key,
        mock_settings_dev_api_enabled,  # noqa: ARG002
    ):
        """Test that sync execution response has correct WorkflowExecutionResponse structure."""
        flow_id = uuid4()

        async with session_scope() as session:
            flow = Flow(
                id=flow_id,
                name="Test Flow",
                description="Flow for response validation",
                data={"nodes": [], "edges": []},
                user_id=created_api_key.user_id,
            )
            session.add(flow)
            await session.flush()
            await session.refresh(flow)

        try:
            request_data = {"flow_id": str(flow_id), "background": False, "stream": False, "inputs": None}

            headers = {"x-api-key": created_api_key.api_key}
            response = await client.post("api/v2/workflows", json=request_data, headers=headers)

            assert response.status_code == 200
            result = response.json()

            # Verify WorkflowExecutionResponse structure
            assert "flow_id" in result
            assert isinstance(result["flow_id"], str)
            assert result["flow_id"] == str(flow_id)

            assert "job_id" in result
            assert isinstance(result["job_id"], str)

            # session_id is optional - only present if provided in inputs
            if "session_id" in result:
                assert isinstance(result["session_id"], str)

            assert "object" in result
            assert result["object"] == "response"

            assert "created_timestamp" in result
            assert isinstance(result["created_timestamp"], str)

            assert "status" in result
            assert result["status"] in ["completed", "failed", "running", "queued"]

            assert "errors" in result
            assert isinstance(result["errors"], list)

            assert "inputs" in result
            assert isinstance(result["inputs"], dict)

            assert "outputs" in result
            assert isinstance(result["outputs"], dict)

        finally:
            async with session_scope() as session:
                flow = await session.get(Flow, flow_id)
                if flow:
                    await session.delete(flow)

        # Test POST /workflow/stop without API key
        response = await client.post(
            "api/v2/workflows/stop",
            json={"job_id": "550e8400-e29b-41d4-a716-446655440001"},
        )
        assert response.status_code == 403
        assert "API key must be passed" in response.json()["detail"]