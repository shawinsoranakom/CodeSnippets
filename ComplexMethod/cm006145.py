async def test_sync_execution_component_error_returns_200_with_error_in_body(
        self,
        client: AsyncClient,
        created_api_key,
        mock_settings_dev_api_enabled,  # noqa: ARG002
    ):
        """Test that component execution errors return 200 with error in response body."""
        flow_id = uuid4()

        async with session_scope() as session:
            flow = Flow(
                id=flow_id,
                name="Test Flow",
                description="Flow for testing component errors",
                data={"nodes": [], "edges": []},
                user_id=created_api_key.user_id,
            )
            session.add(flow)
            await session.flush()
            await session.refresh(flow)

        try:
            request_data = {"flow_id": str(flow_id), "background": False, "stream": False, "inputs": None}

            # Mock run_graph_internal to raise a component execution error
            with patch("langflow.api.v2.workflow.run_graph_internal") as mock_run:
                mock_run.side_effect = Exception("Component execution failed: LLM API key not configured")

                headers = {"x-api-key": created_api_key.api_key}
                response = await client.post("api/v2/workflows", json=request_data, headers=headers)

                # Component errors should return 200 with error in body
                assert response.status_code == 200
                result = response.json()

                # Verify error is in response body (via create_error_response)
                assert "errors" in result
                assert len(result["errors"]) > 0
                assert "Component execution failed" in str(result["errors"][0])
                assert result["status"] == "failed"
                assert result["flow_id"] == str(flow_id)
                assert "job_id" in result

        finally:
            async with session_scope() as session:
                flow = await session.get(Flow, flow_id)
                if flow:
                    await session.delete(flow)