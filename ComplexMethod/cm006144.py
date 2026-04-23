async def test_sync_execution_with_empty_flow_returns_200(
        self,
        client: AsyncClient,
        created_api_key,
        mock_settings_dev_api_enabled,  # noqa: ARG002
    ):
        """Test sync execution with empty flow returns 200 with empty outputs."""
        flow_id = uuid4()

        async with session_scope() as session:
            flow = Flow(
                id=flow_id,
                name="Empty Flow",
                description="Flow with no nodes",
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

            # Verify response structure
            assert "flow_id" in result
            assert result["flow_id"] == str(flow_id)
            assert "job_id" in result

            # Verify outputs or errors are present with actual content
            assert "outputs" in result or "errors" in result
            if "outputs" in result:
                assert isinstance(result["outputs"], dict)
            if "errors" in result:
                assert isinstance(result["errors"], list)
            # session_id is only present if provided in inputs

        finally:
            async with session_scope() as session:
                flow = await session.get(Flow, flow_id)
                if flow:
                    await session.delete(flow)