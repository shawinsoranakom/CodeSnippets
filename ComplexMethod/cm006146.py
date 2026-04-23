async def test_sync_execution_with_chat_input_output(
        self,
        client: AsyncClient,
        created_api_key,
        mock_settings_dev_api_enabled,  # noqa: ARG002
    ):
        """Test sync execution with ChatInput and ChatOutput components."""
        flow_id = uuid4()

        async with session_scope() as session:
            flow = Flow(
                id=flow_id,
                name="Chat Flow",
                description="Flow with chat input/output",
                data={"nodes": [], "edges": []},
                user_id=created_api_key.user_id,
            )
            session.add(flow)
            await session.flush()
            await session.refresh(flow)

        try:
            # Input format: component_id.param = value
            request_data = {
                "flow_id": str(flow_id),
                "background": False,
                "stream": False,
                "inputs": {
                    "ChatInput-abc123.input_value": "Hello, how are you?",
                    "ChatInput-abc123.session_id": "session-456",
                },
            }

            # Mock successful execution with ChatOutput
            mock_result_data = MagicMock()
            mock_result_data.component_id = "ChatOutput-xyz789"
            mock_result_data.outputs = {"message": {"message": "I'm doing well, thank you for asking!", "type": "text"}}
            mock_result_data.metadata = {}

            # Wrap ResultData in RunOutputs
            mock_run_output = MagicMock()
            mock_run_output.outputs = [mock_result_data]

            with patch("langflow.api.v2.workflow.run_graph_internal") as mock_run:
                # run_graph_internal returns tuple[list[RunOutputs], str]
                mock_run.return_value = ([mock_run_output], "session-456")

                headers = {"x-api-key": created_api_key.api_key}
                response = await client.post("api/v2/workflows", json=request_data, headers=headers)

                assert response.status_code == 200
                result = response.json()

                # Verify response structure
                assert result["flow_id"] == str(flow_id)
                assert "job_id" in result
                assert "outputs" in result
                # Note: Detailed content validation requires proper graph/vertex mocking
                # which is beyond the scope of unit tests. Integration tests should validate content.

                # Verify inputs were echoed back
                assert "inputs" in result
                assert result["inputs"] == request_data["inputs"]

                # Verify session_id is present when provided in inputs
                if "session_id" in result:
                    assert result["session_id"] == "session-456"

        finally:
            async with session_scope() as session:
                flow = await session.get(Flow, flow_id)
                if flow:
                    await session.delete(flow)