async def test_background_execution_flow(
        self,
        client: AsyncClient,
        created_api_key,
        mock_settings_dev_api_enabled,  # noqa: ARG002
    ):
        """Test the full background job submission flow."""
        flow_id = uuid4()

        async with session_scope() as session:
            flow = Flow(
                id=flow_id,
                name="Background Flow",
                description="Flow for background testing",
                data={"nodes": [], "edges": []},
                user_id=created_api_key.user_id,
            )
            session.add(flow)
            await session.flush()
            await session.refresh(flow)

        try:
            request_data = {
                "flow_id": str(flow_id),
                "background": True,
                "inputs": {"test.input": "data"},
            }

            headers = {"x-api-key": created_api_key.api_key}

            # Mock uuid4 to return a predictable job_id
            mock_job_id = "550e8400-e29b-41d4-a716-446655440001"
            with (
                patch("langflow.api.v2.workflow.get_task_service") as mock_get_task_service,
                patch("langflow.api.v2.workflow.uuid4", return_value=UUID(mock_job_id)),
            ):
                mock_task_service = MagicMock()
                # fire_and_forget_task is now awaited but its return value is not used for the job_id in response
                # as it uses graph.run_id. However, we still need it to be an awaitable if it's awaited.
                mock_task_service.fire_and_forget_task.return_value = asyncio.Future()
                mock_task_service.fire_and_forget_task.return_value.set_result(mock_job_id)
                mock_get_task_service.return_value = mock_task_service

                response = await client.post("api/v2/workflows", json=request_data, headers=headers)

                assert response.status_code == 200
                result = response.json()

                assert result["job_id"] == mock_job_id
                assert result["flow_id"] == str(flow_id)
                assert result["object"] == "job"
                assert result["status"] == "queued"
                assert "links" in result
                assert "status" in result["links"]
                assert mock_job_id in result["links"]["status"]

        finally:
            async with session_scope() as session:
                flow = await session.get(Flow, flow_id)
                if flow:
                    await session.delete(flow)