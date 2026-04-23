async def test_output_yielding_with_dynamic_fields():
    """Test that outputs are yielded correctly with dynamic field names mapped back."""
    block = OrchestratorBlock()

    # No more sanitized mapping needed since we removed sanitization

    # Mock LLM response with tool calls
    mock_response = Mock()
    mock_response.tool_calls = [
        Mock(
            function=Mock(
                arguments=json.dumps(
                    {
                        "values___name": "Alice",
                        "values___age": 30,
                        "values___email": "alice@example.com",
                    }
                ),
            )
        )
    ]
    # Ensure function name is a real string, not a Mock name
    mock_response.tool_calls[0].function.name = "createdictionaryblock"
    mock_response.reasoning = "Creating a dictionary with user information"
    mock_response.raw_response = {"role": "assistant", "content": "test"}
    mock_response.prompt_tokens = 100
    mock_response.completion_tokens = 50
    mock_response.cache_read_tokens = 0
    mock_response.cache_creation_tokens = 0
    mock_response.provider_cost = None

    # Mock the LLM call
    with patch(
        "backend.blocks.orchestrator.llm.llm_call", new_callable=AsyncMock
    ) as mock_llm:
        mock_llm.return_value = mock_response

        # Mock the database manager to avoid HTTP calls during tool execution
        with patch(
            "backend.blocks.orchestrator.get_database_manager_async_client"
        ) as mock_db_manager, patch.object(
            block, "_create_tool_node_signatures", new_callable=AsyncMock
        ) as mock_sig:
            # Set up the mock database manager
            mock_db_client = AsyncMock()
            mock_db_manager.return_value = mock_db_client

            # Mock the node retrieval
            mock_target_node = Mock()
            mock_target_node.id = "test-sink-node-id"
            mock_target_node.block_id = "CreateDictionaryBlock"
            mock_target_node.block = Mock()
            mock_target_node.block.name = "Create Dictionary"
            mock_db_client.get_node.return_value = mock_target_node

            # Mock the execution result creation
            mock_node_exec_result = Mock()
            mock_node_exec_result.node_exec_id = "mock-node-exec-id"
            mock_final_input_data = {
                "values_#_name": "Alice",
                "values_#_age": 30,
                "values_#_email": "alice@example.com",
            }
            mock_db_client.upsert_execution_input.return_value = (
                mock_node_exec_result,
                mock_final_input_data,
            )

            # Mock the output retrieval
            mock_outputs = {
                "values_#_name": "Alice",
                "values_#_age": 30,
                "values_#_email": "alice@example.com",
            }
            mock_db_client.get_execution_outputs_by_node_exec_id.return_value = (
                mock_outputs
            )

            mock_sig.return_value = [
                {
                    "type": "function",
                    "function": {
                        "name": "createdictionaryblock",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "values___name": {"type": "string"},
                                "values___age": {"type": "number"},
                                "values___email": {"type": "string"},
                            },
                        },
                        "_sink_node_id": "test-sink-node-id",
                    },
                }
            ]

            # Create input data
            from backend.blocks import llm

            input_data = block.input_schema(
                prompt="Create a user dictionary",
                credentials=llm.TEST_CREDENTIALS_INPUT,
                model=llm.DEFAULT_LLM_MODEL,
                agent_mode_max_iterations=0,  # Use traditional mode to test output yielding
            )

            # Run the block
            outputs = {}
            from backend.data.execution import ExecutionContext

            mock_execution_context = ExecutionContext(human_in_the_loop_safe_mode=False)
            mock_execution_processor = MagicMock()

            async for output_name, output_value in block.run(
                input_data,
                credentials=llm.TEST_CREDENTIALS,
                graph_id="test_graph",
                node_id="test_node",
                graph_exec_id="test_exec",
                node_exec_id="test_node_exec",
                user_id="test_user",
                graph_version=1,
                execution_context=mock_execution_context,
                execution_processor=mock_execution_processor,
            ):
                outputs[output_name] = output_value

            # Verify the outputs use sink node ID in output keys
            assert "tools_^_test-sink-node-id_~_values___name" in outputs
            assert outputs["tools_^_test-sink-node-id_~_values___name"] == "Alice"

            assert "tools_^_test-sink-node-id_~_values___age" in outputs
            assert outputs["tools_^_test-sink-node-id_~_values___age"] == 30

            assert "tools_^_test-sink-node-id_~_values___email" in outputs
            assert (
                outputs["tools_^_test-sink-node-id_~_values___email"]
                == "alice@example.com"
            )