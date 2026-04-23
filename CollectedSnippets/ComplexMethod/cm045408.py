async def test_round_robin_group_chat(runtime: AgentRuntime | None) -> None:
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
        )
        expected_messages = [
            "Write a program that prints 'Hello, world!'",
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

        # Test streaming with default output_task_messages=True.
        model_client.reset()
        await team.reset()
        streamed_messages: List[BaseAgentEvent | BaseChatMessage] = []
        final_stream_result: TaskResult | None = None
        async for message in team.run_stream(
            task="Write a program that prints 'Hello, world!'",
        ):
            if isinstance(message, TaskResult):
                final_stream_result = message
            else:
                streamed_messages.append(message)
        assert final_stream_result is not None
        assert compare_task_results(final_stream_result, result)
        # Verify streamed messages match the complete result.messages
        assert len(streamed_messages) == len(result.messages)
        for streamed_msg, expected_msg in zip(streamed_messages, result.messages, strict=False):
            assert compare_messages(streamed_msg, expected_msg)

        # Test message input.
        # Text message.
        model_client.reset()
        await team.reset()
        result_2 = await team.run(
            task=TextMessage(content="Write a program that prints 'Hello, world!'", source="user")
        )
        assert compare_task_results(result, result_2)

        # Test multi-modal message.
        model_client.reset()
        await team.reset()
        task = MultiModalMessage(content=["Write a program that prints 'Hello, world!'"], source="user")
        result_2 = await team.run(task=task)
        assert isinstance(result.messages[0], TextMessage)
        assert isinstance(result_2.messages[0], MultiModalMessage)
        assert result.messages[0].content == task.content[0]
        assert len(result.messages[1:]) == len(result_2.messages[1:])
        for i in range(1, len(result.messages)):
            assert compare_messages(result.messages[i], result_2.messages[i])