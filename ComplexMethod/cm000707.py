async def test_agent_mode_conversation_valid_for_responses_api():
    """Agent mode with a Responses API raw_response: the conversation passed
    to the second LLM call must contain only valid input items.

    Currently fails because:
    1. The full Response object is serialised as a dict without ``role``
    2. Tool results use ``role: "tool"`` instead of ``type: function_call_output``
    """
    import backend.blocks.llm as llm_module

    block = OrchestratorBlock()

    # First response: tool call
    mock_tc = MagicMock()
    mock_tc.id = "call_abc"
    mock_tc.function.name = "story_improver"
    mock_tc.function.arguments = (
        '{"prompt_values___story": "draft", "prompt_values___improvement": "polish"}'
    )

    resp1 = MagicMock()
    resp1.response = None
    resp1.tool_calls = [mock_tc]
    resp1.prompt_tokens = 100
    resp1.completion_tokens = 50
    resp1.reasoning = None
    resp1.raw_response = _MockResponse(
        output=[
            _MockFunctionCall(
                "story_improver",
                '{"prompt_values___story": "draft", "prompt_values___improvement": "polish"}',
                call_id="call_abc",
            )
        ]
    )

    # Second response: finished
    resp2 = MagicMock()
    resp2.response = "Done!"
    resp2.tool_calls = []
    resp2.prompt_tokens = 200
    resp2.completion_tokens = 10
    resp2.reasoning = None
    resp2.raw_response = _MockResponse(output=[_MockOutputMessage("Done!")])

    llm_mock = AsyncMock(side_effect=[resp1, resp2])

    tool_sigs = [
        {
            "type": "function",
            "function": {
                "name": "story_improver",
                "_sink_node_id": "sink-1",
                "_field_mapping": {},
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt_values___story": {"type": "string"},
                        "prompt_values___improvement": {"type": "string"},
                    },
                    "required": [
                        "prompt_values___story",
                        "prompt_values___improvement",
                    ],
                },
            },
        }
    ]

    mock_db = AsyncMock()
    mock_db.get_node.return_value = MagicMock(block_id="bid")
    ner = MagicMock(node_exec_id="neid")
    mock_db.upsert_execution_input.return_value = (
        ner,
        {"prompt_values___story": "draft", "prompt_values___improvement": "polish"},
    )
    mock_db.get_execution_outputs_by_node_exec_id.return_value = {
        "response": "polished"
    }

    ep = AsyncMock()
    ep.running_node_execution = defaultdict(MagicMock)
    ep.execution_stats = MagicMock()
    ep.execution_stats_lock = threading.Lock()
    ns = MagicMock(error=None)
    ep.on_node_execution = AsyncMock(return_value=ns)
    # Mock charge_node_usage (called after successful tool execution).
    # Must be AsyncMock because it is async and is awaited in
    # _execute_single_tool_with_manager — a plain MagicMock would return a
    # non-awaitable tuple and TypeError out, then be silently swallowed by
    # the orchestrator's catch-all.
    ep.charge_node_usage = AsyncMock(return_value=(0, 0))

    with patch("backend.blocks.llm.llm_call", llm_mock), patch.object(
        block, "_create_tool_node_signatures", return_value=tool_sigs
    ), patch(
        "backend.blocks.orchestrator.get_database_manager_async_client",
        return_value=mock_db,
    ), patch(
        "backend.executor.manager.async_update_node_execution_status",
        new_callable=AsyncMock,
    ), patch(
        "backend.integrations.creds_manager.IntegrationCredentialsManager"
    ):

        inp = OrchestratorBlock.Input(
            prompt="Improve this",
            model=llm_module.DEFAULT_LLM_MODEL,
            credentials=llm_module.TEST_CREDENTIALS_INPUT,  # type: ignore
            agent_mode_max_iterations=5,
        )

        outputs = {}
        async for name, data in block.run(
            inp,
            credentials=llm_module.TEST_CREDENTIALS,
            graph_id="gid",
            node_id="nid",
            graph_exec_id="geid",
            node_exec_id="neid",
            user_id="uid",
            graph_version=1,
            execution_context=ExecutionContext(human_in_the_loop_safe_mode=False),
            execution_processor=ep,
        ):
            outputs[name] = data

        # The second LLM call's prompt must only contain valid items
        assert llm_mock.call_count >= 2
        second_call = llm_mock.call_args_list[1]
        second_prompt = second_call.kwargs.get("prompt")
        if second_prompt is None:
            second_prompt = second_call[0][1] if len(second_call[0]) > 1 else None
        assert second_prompt is not None

        for i, item in enumerate(second_prompt):
            has_role = item.get("role") in ("assistant", "system", "user", "developer")
            has_type = item.get("type") in (
                "function_call",
                "function_call_output",
                "message",
            )
            assert (
                has_role or has_type
            ), f"input[{i}] has neither valid role nor type: {item!r}"