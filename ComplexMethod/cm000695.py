async def test_orchestrator_agent_mode():
    """Test that agent mode executes tools directly and loops until finished."""
    import backend.blocks.llm as llm_module
    from backend.blocks.orchestrator import OrchestratorBlock

    block = OrchestratorBlock()

    # Mock tool call that requires multiple iterations
    mock_tool_call_1 = MagicMock()
    mock_tool_call_1.id = "call_1"
    mock_tool_call_1.function.name = "search_keywords"
    mock_tool_call_1.function.arguments = (
        '{"query": "test", "max_keyword_difficulty": 50}'
    )

    mock_response_1 = MagicMock()
    mock_response_1.response = None
    mock_response_1.tool_calls = [mock_tool_call_1]
    mock_response_1.prompt_tokens = 50
    mock_response_1.completion_tokens = 25
    mock_response_1.reasoning = "Using search tool"
    mock_response_1.raw_response = {
        "role": "assistant",
        "content": None,
        "tool_calls": [{"id": "call_1", "type": "function"}],
    }

    # Final response with no tool calls (finished)
    mock_response_2 = MagicMock()
    mock_response_2.response = "Task completed successfully"
    mock_response_2.tool_calls = []
    mock_response_2.prompt_tokens = 30
    mock_response_2.completion_tokens = 15
    mock_response_2.reasoning = None
    mock_response_2.raw_response = {
        "role": "assistant",
        "content": "Task completed successfully",
    }

    # Mock the LLM call to return different responses on each iteration
    llm_call_mock = AsyncMock()
    llm_call_mock.side_effect = [mock_response_1, mock_response_2]

    # Mock tool node signatures
    mock_tool_signatures = [
        {
            "type": "function",
            "function": {
                "name": "search_keywords",
                "_sink_node_id": "test-sink-node-id",
                "_field_mapping": {},
                "parameters": {
                    "properties": {
                        "query": {"type": "string"},
                        "max_keyword_difficulty": {"type": "integer"},
                    },
                    "required": ["query", "max_keyword_difficulty"],
                },
            },
        }
    ]

    # Mock database and execution components
    mock_db_client = AsyncMock()
    mock_node = MagicMock()
    mock_node.block_id = "test-block-id"
    mock_db_client.get_node.return_value = mock_node

    # Mock upsert_execution_input to return proper NodeExecutionResult and input data
    mock_node_exec_result = MagicMock()
    mock_node_exec_result.node_exec_id = "test-tool-exec-id"
    mock_input_data = {"query": "test", "max_keyword_difficulty": 50}
    mock_db_client.upsert_execution_input.return_value = (
        mock_node_exec_result,
        mock_input_data,
    )

    # No longer need mock_execute_node since we use execution_processor.on_node_execution

    with patch("backend.blocks.llm.llm_call", llm_call_mock), patch.object(
        block, "_create_tool_node_signatures", return_value=mock_tool_signatures
    ), patch(
        "backend.blocks.orchestrator.get_database_manager_async_client",
        return_value=mock_db_client,
    ), patch(
        "backend.executor.manager.async_update_node_execution_status",
        new_callable=AsyncMock,
    ), patch(
        "backend.integrations.creds_manager.IntegrationCredentialsManager"
    ):

        # Create a mock execution context

        mock_execution_context = ExecutionContext(
            human_in_the_loop_safe_mode=False,
        )

        # Create a mock execution processor for agent mode tests

        mock_execution_processor = AsyncMock()
        # Configure the execution processor mock with required attributes
        mock_execution_processor.running_node_execution = defaultdict(MagicMock)
        mock_execution_processor.execution_stats = MagicMock()
        mock_execution_processor.execution_stats_lock = threading.Lock()

        # Mock the on_node_execution method to return successful stats
        mock_node_stats = MagicMock()
        mock_node_stats.error = None  # No error
        mock_execution_processor.on_node_execution = AsyncMock(
            return_value=mock_node_stats
        )
        # Mock charge_node_usage (called after successful tool execution).
        # Returns (cost, remaining_balance). Must be AsyncMock because it is
        # an async method and is directly awaited in _execute_single_tool_with_manager.
        # Use a non-zero cost so the merge_stats branch is exercised.
        mock_execution_processor.charge_node_usage = AsyncMock(return_value=(10, 990))

        # Mock the get_execution_outputs_by_node_exec_id method
        mock_db_client.get_execution_outputs_by_node_exec_id.return_value = {
            "result": {"status": "success", "data": "search completed"}
        }

        # Test agent mode with max_iterations = 3
        input_data = OrchestratorBlock.Input(
            prompt="Complete this task using tools",
            model=llm_module.DEFAULT_LLM_MODEL,
            credentials=llm_module.TEST_CREDENTIALS_INPUT,  # type: ignore
            agent_mode_max_iterations=3,  # Enable agent mode with 3 max iterations
        )

        outputs = {}
        async for output_name, output_data in block.run(
            input_data,
            credentials=llm_module.TEST_CREDENTIALS,
            graph_id="test-graph-id",
            node_id="test-node-id",
            graph_exec_id="test-exec-id",
            node_exec_id="test-node-exec-id",
            user_id="test-user-id",
            graph_version=1,
            execution_context=mock_execution_context,
            execution_processor=mock_execution_processor,
        ):
            outputs[output_name] = output_data

        # Verify agent mode behavior
        assert "tool_functions" in outputs  # tool_functions is yielded in both modes
        assert "finished" in outputs
        assert outputs["finished"] == "Task completed successfully"
        assert "conversations" in outputs

        # Verify the conversation includes tool responses
        conversations = outputs["conversations"]
        assert len(conversations) > 2  # Should have multiple conversation entries

        # Verify LLM was called twice (once for tool call, once for finish)
        assert llm_call_mock.call_count == 2

        # Verify tool was executed via execution processor
        assert mock_execution_processor.on_node_execution.call_count == 1

        # Verify charge_node_usage was actually called for the successful
        # tool execution — this guards against regressions where the
        # post-execution tool charging is accidentally removed.
        assert mock_execution_processor.charge_node_usage.call_count == 1