async def test_output_task_messages_false(self) -> None:
        """Test agent with output_task_messages=False.

        Verifies that:
        1. Task messages are excluded from result when output_task_messages=False
        2. Only agent response messages are included in output
        3. Both run and run_stream respect the parameter
        """
        model_client = ReplayChatCompletionClient(
            [
                CreateResult(
                    finish_reason="stop",
                    content="Agent response without task message",
                    usage=RequestUsage(prompt_tokens=10, completion_tokens=8),
                    cached=False,
                ),
                CreateResult(
                    finish_reason="stop",
                    content="Second agent response",
                    usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
                    cached=False,
                ),
            ],
            model_info={
                "function_calling": False,
                "vision": False,
                "json_output": False,
                "family": ModelFamily.GPT_4O,
                "structured_output": False,
            },
        )

        agent = AssistantAgent(name="test_agent", model_client=model_client)

        # Test run() with output_task_messages=False
        result = await agent.run(task="Test task message", output_task_messages=False)

        # Should only contain the agent's response, not the task message
        assert len(result.messages) == 1
        assert isinstance(result.messages[0], TextMessage)
        assert result.messages[0].content == "Agent response without task message"
        assert result.messages[0].source == "test_agent"  # Test run_stream() with output_task_messages=False
        # Create a new model client for streaming test to avoid response conflicts
        stream_model_client = ReplayChatCompletionClient(
            [
                CreateResult(
                    finish_reason="stop",
                    content="Stream agent response",
                    usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
                    cached=False,
                ),
            ],
            model_info={
                "function_calling": False,
                "vision": False,
                "json_output": False,
                "family": ModelFamily.GPT_4O,
                "structured_output": False,
            },
        )

        stream_agent = AssistantAgent(name="test_agent", model_client=stream_model_client)
        streamed_messages: List[BaseAgentEvent | BaseChatMessage] = []
        final_result: TaskResult | None = None

        async for message in stream_agent.run_stream(task="Test task message", output_task_messages=False):
            if isinstance(message, TaskResult):
                final_result = message
            else:
                streamed_messages.append(message)

        # Verify streaming behavior
        assert final_result is not None
        assert len(final_result.messages) == 1
        assert isinstance(final_result.messages[0], TextMessage)
        assert final_result.messages[0].content == "Stream agent response"

        # Verify that no task message was streamed
        task_messages = [msg for msg in streamed_messages if isinstance(msg, TextMessage) and msg.source == "user"]
        assert len(task_messages) == 0  # Test with multiple task messages
        multi_model_client = ReplayChatCompletionClient(
            [
                CreateResult(
                    finish_reason="stop",
                    content="Multi task response",
                    usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
                    cached=False,
                ),
            ],
            model_info={
                "function_calling": False,
                "vision": False,
                "json_output": False,
                "family": ModelFamily.GPT_4O,
                "structured_output": False,
            },
        )

        multi_agent = AssistantAgent(name="test_agent", model_client=multi_model_client)
        task_messages_list = [
            TextMessage(content="First task", source="user"),
            TextMessage(content="Second task", source="user"),
        ]

        result_multi = await multi_agent.run(task=task_messages_list, output_task_messages=False)

        # Should only contain the agent's response, not the multiple task messages
        assert len(result_multi.messages) == 1
        assert isinstance(result_multi.messages[0], TextMessage)
        assert result_multi.messages[0].source == "test_agent"
        assert result_multi.messages[0].content == "Multi task response"