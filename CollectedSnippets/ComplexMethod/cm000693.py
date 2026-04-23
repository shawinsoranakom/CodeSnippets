async def test_orchestrator_parameter_validation():
    """Test that OrchestratorBlock correctly validates tool call parameters."""
    import backend.blocks.llm as llm_module
    from backend.blocks.orchestrator import OrchestratorBlock

    block = OrchestratorBlock()

    # Mock tool functions with specific parameter schema
    mock_tool_functions = [
        {
            "type": "function",
            "function": {
                "name": "search_keywords",
                "description": "Search for keywords with difficulty filtering",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_keyword_difficulty": {
                            "type": "integer",
                            "description": "Maximum keyword difficulty (required)",
                        },
                        "optional_param": {
                            "type": "string",
                            "description": "Optional parameter with default",
                            "default": "default_value",
                        },
                    },
                    "required": ["query", "max_keyword_difficulty"],
                },
                "_sink_node_id": "test-sink-node-id",
            },
        }
    ]

    # Test case 1: Tool call with TYPO in parameter name (should retry and eventually fail)
    mock_tool_call_with_typo = MagicMock()
    mock_tool_call_with_typo.function.name = "search_keywords"
    mock_tool_call_with_typo.function.arguments = '{"query": "test", "maximum_keyword_difficulty": 50}'  # TYPO: maximum instead of max

    mock_response_with_typo = MagicMock()
    mock_response_with_typo.response = None
    mock_response_with_typo.tool_calls = [mock_tool_call_with_typo]
    mock_response_with_typo.prompt_tokens = 50
    mock_response_with_typo.completion_tokens = 25
    mock_response_with_typo.reasoning = None
    mock_response_with_typo.raw_response = {"role": "assistant", "content": None}

    with patch(
        "backend.blocks.llm.llm_call",
        new_callable=AsyncMock,
        return_value=mock_response_with_typo,
    ) as mock_llm_call, patch.object(
        OrchestratorBlock,
        "_create_tool_node_signatures",
        new_callable=AsyncMock,
        return_value=mock_tool_functions,
    ):

        input_data = OrchestratorBlock.Input(
            prompt="Search for keywords",
            model=llm_module.DEFAULT_LLM_MODEL,
            credentials=llm_module.TEST_CREDENTIALS_INPUT,  # type: ignore
            retry=2,  # Set retry to 2 for testing
            agent_mode_max_iterations=0,
        )

        # Create execution context

        mock_execution_context = ExecutionContext(human_in_the_loop_safe_mode=False)

        # Create a mock execution processor for tests

        mock_execution_processor = MagicMock()

        # Should raise ValueError after retries due to typo'd parameter name
        with pytest.raises(ValueError) as exc_info:
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

        # Verify error message contains details about the typo
        error_msg = str(exc_info.value)
        assert "Tool call 'search_keywords' has parameter errors" in error_msg
        assert "Unknown parameters: ['maximum_keyword_difficulty']" in error_msg

        # Verify that LLM was called the expected number of times (retries)
        assert mock_llm_call.call_count == 2  # Should retry based on input_data.retry

    # Test case 2: Tool call missing REQUIRED parameter (should raise ValueError)
    mock_tool_call_missing_required = MagicMock()
    mock_tool_call_missing_required.function.name = "search_keywords"
    mock_tool_call_missing_required.function.arguments = (
        '{"query": "test"}'  # Missing required max_keyword_difficulty
    )

    mock_response_missing_required = MagicMock()
    mock_response_missing_required.response = None
    mock_response_missing_required.tool_calls = [mock_tool_call_missing_required]
    mock_response_missing_required.prompt_tokens = 50
    mock_response_missing_required.completion_tokens = 25
    mock_response_missing_required.reasoning = None
    mock_response_missing_required.raw_response = {"role": "assistant", "content": None}

    with patch(
        "backend.blocks.llm.llm_call",
        new_callable=AsyncMock,
        return_value=mock_response_missing_required,
    ), patch.object(
        OrchestratorBlock,
        "_create_tool_node_signatures",
        new_callable=AsyncMock,
        return_value=mock_tool_functions,
    ):

        input_data = OrchestratorBlock.Input(
            prompt="Search for keywords",
            model=llm_module.DEFAULT_LLM_MODEL,
            credentials=llm_module.TEST_CREDENTIALS_INPUT,  # type: ignore
            agent_mode_max_iterations=0,
        )

        # Create execution context

        mock_execution_context = ExecutionContext(human_in_the_loop_safe_mode=False)

        # Create a mock execution processor for tests

        mock_execution_processor = MagicMock()

        # Should raise ValueError due to missing required parameter
        with pytest.raises(ValueError) as exc_info:
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

        error_msg = str(exc_info.value)
        assert "Tool call 'search_keywords' has parameter errors" in error_msg
        assert "Missing required parameters: ['max_keyword_difficulty']" in error_msg

    # Test case 3: Valid tool call with OPTIONAL parameter missing (should succeed)
    mock_tool_call_valid = MagicMock()
    mock_tool_call_valid.function.name = "search_keywords"
    mock_tool_call_valid.function.arguments = '{"query": "test", "max_keyword_difficulty": 50}'  # optional_param missing, but that's OK

    mock_response_valid = MagicMock()
    mock_response_valid.response = None
    mock_response_valid.tool_calls = [mock_tool_call_valid]
    mock_response_valid.prompt_tokens = 50
    mock_response_valid.completion_tokens = 25
    mock_response_valid.reasoning = None
    mock_response_valid.raw_response = {"role": "assistant", "content": None}

    with patch(
        "backend.blocks.llm.llm_call",
        new_callable=AsyncMock,
        return_value=mock_response_valid,
    ), patch.object(
        OrchestratorBlock,
        "_create_tool_node_signatures",
        new_callable=AsyncMock,
        return_value=mock_tool_functions,
    ):

        input_data = OrchestratorBlock.Input(
            prompt="Search for keywords",
            model=llm_module.DEFAULT_LLM_MODEL,
            credentials=llm_module.TEST_CREDENTIALS_INPUT,  # type: ignore
            agent_mode_max_iterations=0,
        )

        # Should succeed - optional parameter missing is OK
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

        # Verify tool outputs were generated correctly
        assert "tools_^_test-sink-node-id_~_query" in outputs
        assert outputs["tools_^_test-sink-node-id_~_query"] == "test"
        assert "tools_^_test-sink-node-id_~_max_keyword_difficulty" in outputs
        assert outputs["tools_^_test-sink-node-id_~_max_keyword_difficulty"] == 50
        # Optional parameter should be None when not provided
        assert "tools_^_test-sink-node-id_~_optional_param" in outputs
        assert outputs["tools_^_test-sink-node-id_~_optional_param"] is None

    # Test case 4: Valid tool call with ALL parameters (should succeed)
    mock_tool_call_all_params = MagicMock()
    mock_tool_call_all_params.function.name = "search_keywords"
    mock_tool_call_all_params.function.arguments = '{"query": "test", "max_keyword_difficulty": 50, "optional_param": "custom_value"}'

    mock_response_all_params = MagicMock()
    mock_response_all_params.response = None
    mock_response_all_params.tool_calls = [mock_tool_call_all_params]
    mock_response_all_params.prompt_tokens = 50
    mock_response_all_params.completion_tokens = 25
    mock_response_all_params.reasoning = None
    mock_response_all_params.raw_response = {"role": "assistant", "content": None}

    with patch(
        "backend.blocks.llm.llm_call",
        new_callable=AsyncMock,
        return_value=mock_response_all_params,
    ), patch.object(
        OrchestratorBlock,
        "_create_tool_node_signatures",
        new_callable=AsyncMock,
        return_value=mock_tool_functions,
    ):

        input_data = OrchestratorBlock.Input(
            prompt="Search for keywords",
            model=llm_module.DEFAULT_LLM_MODEL,
            credentials=llm_module.TEST_CREDENTIALS_INPUT,  # type: ignore
            agent_mode_max_iterations=0,
        )

        # Should succeed with all parameters
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

        # Verify all tool outputs were generated correctly
        assert outputs["tools_^_test-sink-node-id_~_query"] == "test"
        assert outputs["tools_^_test-sink-node-id_~_max_keyword_difficulty"] == 50
        assert outputs["tools_^_test-sink-node-id_~_optional_param"] == "custom_value"