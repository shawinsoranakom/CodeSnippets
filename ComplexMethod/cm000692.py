async def test_orchestrator_tracks_llm_stats():
    """Test that OrchestratorBlock correctly tracks LLM usage stats."""
    import backend.blocks.llm as llm_module
    from backend.blocks.orchestrator import OrchestratorBlock

    block = OrchestratorBlock()

    # Mock the llm.llm_call function to return controlled data
    mock_response = MagicMock()
    mock_response.response = "I need to think about this."
    mock_response.tool_calls = None  # No tool calls for simplicity
    mock_response.prompt_tokens = 50
    mock_response.completion_tokens = 25
    mock_response.reasoning = None
    mock_response.raw_response = {
        "role": "assistant",
        "content": "I need to think about this.",
    }

    # Mock the _create_tool_node_signatures method to avoid database calls

    with patch(
        "backend.blocks.llm.llm_call",
        new_callable=AsyncMock,
        return_value=mock_response,
    ), patch.object(
        OrchestratorBlock,
        "_create_tool_node_signatures",
        new_callable=AsyncMock,
        return_value=[],
    ):

        # Create test input
        input_data = OrchestratorBlock.Input(
            prompt="Should I continue with this task?",
            model=llm_module.DEFAULT_LLM_MODEL,
            credentials=llm_module.TEST_CREDENTIALS_INPUT,  # type: ignore
            agent_mode_max_iterations=0,
        )

        # Execute the block
        outputs = {}
        # Create execution context

        mock_execution_context = ExecutionContext(human_in_the_loop_safe_mode=False)

        # Create a mock execution processor for tests

        mock_execution_processor = MagicMock()

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

        # Verify stats tracking
        assert block.execution_stats is not None
        assert block.execution_stats.input_token_count == 50
        assert block.execution_stats.output_token_count == 25
        assert block.execution_stats.llm_call_count == 1

        # Verify outputs
        assert "finished" in outputs  # Should have finished since no tool calls
        assert outputs["finished"] == "I need to think about this."