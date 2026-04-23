async def test_round_robin_group_chat_output_task_messages_false(runtime: AgentRuntime | None) -> None:
    model_client = ReplayChatCompletionClient(
        [
            'Here is the program\n ```python\nprint("Hello, world!")\n```',
            "TERMINATE",
        ],
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        code_executor_agent = CodeExecutorAgent(
            "code_executor", code_executor=LocalCommandLineCodeExecutor(work_dir=temp_dir)
        )
        coding_assistant_agent = AssistantAgent(
            "coding_assistant",
            model_client=model_client,
        )
        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat(
            participants=[coding_assistant_agent, code_executor_agent],
            termination_condition=termination,
            runtime=runtime,
        )
        result = await team.run(
            task="Write a program that prints 'Hello, world!'",
            output_task_messages=False,
        )
        expected_messages = [
            'Here is the program\n ```python\nprint("Hello, world!")\n```',
            "Hello, world!",
            "TERMINATE",
        ]
        for i in range(len(expected_messages)):
            produced_message = result.messages[i]
            assert isinstance(produced_message, TextMessage)
            content = produced_message.content.replace("\r\n", "\n").rstrip("\n")
            assert content == expected_messages[i]

        assert result.stop_reason is not None and result.stop_reason == "Text 'TERMINATE' mentioned"

        # Test streaming with output_task_messages=False.
        model_client.reset()
        await team.reset()
        streamed_messages: List[BaseAgentEvent | BaseChatMessage] = []
        final_stream_result: TaskResult | None = None
        async for message in team.run_stream(
            task="Write a program that prints 'Hello, world!'",
            output_task_messages=False,
        ):
            if isinstance(message, TaskResult):
                final_stream_result = message
            else:
                streamed_messages.append(message)
        assert final_stream_result is not None
        assert compare_task_results(final_stream_result, result)
        # Verify streamed messages match the complete result.messages excluding the first task message
        assert len(streamed_messages) == len(result.messages)  # Exclude task message
        for streamed_msg, expected_msg in zip(streamed_messages, result.messages, strict=False):
            assert compare_messages(streamed_msg, expected_msg)

        # Test message input with output_task_messages=False.
        # Text message.
        model_client.reset()
        await team.reset()
        streamed_messages_2: List[BaseAgentEvent | BaseChatMessage] = []
        final_stream_result_2: TaskResult | None = None
        async for message in team.run_stream(
            task=TextMessage(content="Write a program that prints 'Hello, world!'", source="user"),
            output_task_messages=False,
        ):
            if isinstance(message, TaskResult):
                final_stream_result_2 = message
            else:
                streamed_messages_2.append(message)
        assert final_stream_result_2 is not None
        assert compare_task_results(final_stream_result_2, result)
        # Verify streamed messages match the complete result.messages excluding the first task message
        assert len(streamed_messages_2) == len(result.messages)
        for streamed_msg, expected_msg in zip(streamed_messages_2, result.messages, strict=False):
            assert compare_messages(streamed_msg, expected_msg)

        # Test multi-modal message with output_task_messages=False.
        model_client.reset()
        await team.reset()
        task = MultiModalMessage(content=["Write a program that prints 'Hello, world!'"], source="user")
        streamed_messages_3: List[BaseAgentEvent | BaseChatMessage] = []
        final_stream_result_3: TaskResult | None = None
        async for message in team.run_stream(task=task, output_task_messages=False):
            if isinstance(message, TaskResult):
                final_stream_result_3 = message
            else:
                streamed_messages_3.append(message)
        assert final_stream_result_3 is not None
        # Verify streamed messages exclude the task message
        assert len(streamed_messages_3) == len(final_stream_result_3.messages)
        for streamed_msg, expected_msg in zip(streamed_messages_3, final_stream_result_3.messages, strict=False):
            assert compare_messages(streamed_msg, expected_msg)