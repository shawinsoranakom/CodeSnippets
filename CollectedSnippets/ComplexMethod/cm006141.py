async def test_execute_workflow_allowed_when_dev_api_enabled_flow_exists(
        self,
        client: AsyncClient,
        created_api_key,
        mock_settings_dev_api_enabled,  # noqa: ARG002
    ):
        """Test POST /workflow allowed when dev API enabled - flow exists and executes."""
        flow_id = uuid4()

        # Create a flow in the database using the established pattern
        async with session_scope() as session:
            flow = Flow(
                id=flow_id,
                name="Test Flow",
                description="Test flow for API testing",
                data={"nodes": [], "edges": []},
                user_id=created_api_key.user_id,
            )
            session.add(flow)
            await session.flush()
            await session.refresh(flow)

        try:
            request_data = {"flow_id": str(flow.id), "background": False, "stream": False, "inputs": None}

            headers = {"x-api-key": created_api_key.api_key}
            response = await client.post(
                "api/v2/workflows",
                json=request_data,
                headers=headers,
            )

            # Should return 200 because flow is valid (empty nodes/edges is valid)
            # The execution will complete successfully with no outputs
            assert response.status_code == 200
            result = response.json()

            # Verify response contains expected fields with proper structure
            assert "outputs" in result or "errors" in result
            if "outputs" in result:
                assert isinstance(result["outputs"], dict)
            if "errors" in result:
                assert isinstance(result["errors"], list)

        finally:
            # Clean up the flow following established pattern
            async with session_scope() as session:
                flow = await session.get(Flow, flow_id)
                if flow:
                    await session.delete(flow)