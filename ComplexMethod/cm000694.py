async def test_orchestrator_raw_response_conversion():
    """Test that Orchestrator correctly handles different raw_response types with retry mechanism."""
    import backend.blocks.llm as llm_module
    from backend.blocks.orchestrator import OrchestratorBlock

    block = OrchestratorBlock()

    # Mock tool functions
    mock_tool_functions = [
        {
            "type": "function",
            "function": {
                "name": "test_tool",
                "parameters": {
                    "type": "object",
                    "properties": {"param": {"type": "string"}},
                    "required": ["param"],
                },
                "_sink_node_id": "test-sink-node-id",
            },
        }
    ]

    # Test case 1: Simulate ChatCompletionMessage raw_response that caused the original error
    class MockChatCompletionMessage:
        """Simulate OpenAI's ChatCompletionMessage object that lacks .get() method"""

        def __init__(self, role, content, tool_calls=None):
            self.role = role
            self.content = content
            self.tool_calls = tool_calls or []

        # This is what caused the error - no .get() method
        # def get(self, key, default=None):  # Intentionally missing

    # First response: has invalid parameter name (triggers retry)
    mock_tool_call_invalid = MagicMock()
    mock_tool_call_invalid.function.name = "test_tool"
    mock_tool_call_invalid.function.arguments = (
        '{"wrong_param": "test_value"}'  # Invalid parameter name
    )

    mock_response_retry = MagicMock()
    mock_response_retry.response = None
    mock_response_retry.tool_calls = [mock_tool_call_invalid]
    mock_response_retry.prompt_tokens = 50
    mock_response_retry.completion_tokens = 25
    mock_response_retry.reasoning = None
    # This would cause the original error without our fix
    mock_response_retry.raw_response = MockChatCompletionMessage(
        role="assistant", content=None, tool_calls=[mock_tool_call_invalid]
    )

    # Second response: successful (correct parameter name)
    mock_tool_call_valid = MagicMock()
    mock_tool_call_valid.function.name = "test_tool"
    mock_tool_call_valid.function.arguments = (
        '{"param": "test_value"}'  # Correct parameter name
    )

    mock_response_success = MagicMock()
    mock_response_success.response = None
    mock_response_success.tool_calls = [mock_tool_call_valid]
    mock_response_success.prompt_tokens = 50
    mock_response_success.completion_tokens = 25
    mock_response_success.reasoning = None
    mock_response_success.raw_response = MockChatCompletionMessage(
        role="assistant", content=None, tool_calls=[mock_tool_call_valid]
    )

    # Mock llm_call to return different responses on different calls

    with patch(
        "backend.blocks.llm.llm_call", new_callable=AsyncMock
    ) as mock_llm_call, patch.object(
        OrchestratorBlock,
        "_create_tool_node_signatures",
        new_callable=AsyncMock,
        return_value=mock_tool_functions,
    ):
        # First call returns response that will trigger retry due to validation error
        # Second call returns successful response
        mock_llm_call.side_effect = [mock_response_retry, mock_response_success]

        input_data = OrchestratorBlock.Input(
            prompt="Test prompt",
            model=llm_module.DEFAULT_LLM_MODEL,
            credentials=llm_module.TEST_CREDENTIALS_INPUT,  # type: ignore
            retry=2,
            agent_mode_max_iterations=0,
        )

        # Should succeed after retry, demonstrating our helper function works
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

        # Verify the tool output was generated successfully
        assert "tools_^_test-sink-node-id_~_param" in outputs
        assert outputs["tools_^_test-sink-node-id_~_param"] == "test_value"

        # Verify conversation history was properly maintained
        assert "conversations" in outputs
        conversations = outputs["conversations"]
        assert len(conversations) > 0

        # The conversations should contain properly converted raw_response objects as dicts
        # This would have failed with the original bug due to ChatCompletionMessage.get() error
        for msg in conversations:
            assert isinstance(msg, dict), f"Expected dict, got {type(msg)}"
            if msg.get("role") == "assistant":
                # Should have been converted from ChatCompletionMessage to dict
                assert "role" in msg

        # Verify LLM was called twice (initial + 1 retry)
        assert mock_llm_call.call_count == 2

    # Test case 2: Test with different raw_response types (Ollama string, dict)
    # Test Ollama string response
    mock_response_ollama = MagicMock()
    mock_response_ollama.response = "I'll help you with that."
    mock_response_ollama.tool_calls = None
    mock_response_ollama.prompt_tokens = 30
    mock_response_ollama.completion_tokens = 15
    mock_response_ollama.reasoning = None
    mock_response_ollama.raw_response = (
        "I'll help you with that."  # Ollama returns string
    )

    with patch(
        "backend.blocks.llm.llm_call",
        new_callable=AsyncMock,
        return_value=mock_response_ollama,
    ), patch.object(
        OrchestratorBlock,
        "_create_tool_node_signatures",
        new_callable=AsyncMock,
        return_value=[],  # No tools for this test
    ):
        input_data = OrchestratorBlock.Input(
            prompt="Simple prompt",
            model=llm_module.DEFAULT_LLM_MODEL,
            credentials=llm_module.TEST_CREDENTIALS_INPUT,  # type: ignore
            agent_mode_max_iterations=0,
        )

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

        # Should finish since no tool calls
        assert "finished" in outputs
        assert outputs["finished"] == "I'll help you with that."

    # Test case 3: Test with dict raw_response (some providers/tests)
    mock_response_dict = MagicMock()
    mock_response_dict.response = "Test response"
    mock_response_dict.tool_calls = None
    mock_response_dict.prompt_tokens = 25
    mock_response_dict.completion_tokens = 10
    mock_response_dict.reasoning = None
    mock_response_dict.raw_response = {
        "role": "assistant",
        "content": "Test response",
    }  # Dict format

    with patch(
        "backend.blocks.llm.llm_call",
        new_callable=AsyncMock,
        return_value=mock_response_dict,
    ), patch.object(
        OrchestratorBlock,
        "_create_tool_node_signatures",
        new_callable=AsyncMock,
        return_value=[],
    ):
        input_data = OrchestratorBlock.Input(
            prompt="Another test",
            model=llm_module.DEFAULT_LLM_MODEL,
            credentials=llm_module.TEST_CREDENTIALS_INPUT,  # type: ignore
            agent_mode_max_iterations=0,
        )

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

        assert "finished" in outputs
        assert outputs["finished"] == "Test response"