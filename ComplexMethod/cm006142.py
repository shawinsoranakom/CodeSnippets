async def test_background_mode_returns_501(
        self,
        client: AsyncClient,
        created_api_key,
        mock_settings_dev_api_enabled,  # noqa: ARG002
    ):
        """Test that background mode returns 501 with NOT_IMPLEMENTED code."""
        flow_id = uuid4()

        # Create a valid flow
        async with session_scope() as session:
            flow = Flow(
                id=flow_id,
                name="Test Flow",
                description="Test flow",
                data={"nodes": [], "edges": []},
                user_id=created_api_key.user_id,
            )
            session.add(flow)
            await session.flush()
            await session.refresh(flow)

        try:
            request_data = {
                "flow_id": str(flow_id),
                "background": True,  # Background mode
                "stream": False,
                "inputs": None,
            }

            headers = {"x-api-key": created_api_key.api_key}
            response = await client.post("api/v2/workflows", json=request_data, headers=headers)

            # Now background mode is partially implemented and should NOT return 501
            # It should return a WorkflowJobResponse (wrapped in WorkflowExecutionResponse or similar)
            assert response.status_code == 200
            result = response.json()
            assert result["object"] == "job"
            assert result["status"] == "queued"
            assert result["flow_id"] == str(flow_id)
            assert "links" in result
            assert "status" in result["links"]

        finally:
            # Clean up
            async with session_scope() as session:
                flow = await session.get(Flow, flow_id)
                if flow:
                    await session.delete(flow)