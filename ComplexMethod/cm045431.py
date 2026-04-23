async def test_selector_group_chat_nested_teams_run_stream(runtime: AgentRuntime | None) -> None:
    """Test SelectorGroupChat with nested teams using run_stream method."""
    model_client = ReplayChatCompletionClient(
        [
            "InnerTeam",  # Select inner team first
            'Here is the program\n ```python\nprint("Hello, world!")\n```',
            "TERMINATE",
            "agent3",  # Select agent3 (reviewer)
            "Good job",
            "TERMINATE",
        ],
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        code_executor = LocalCommandLineCodeExecutor(work_dir=temp_dir)
        assistant = AssistantAgent(
            "assistant",
            model_client=model_client,
            description="An assistant agent that writes code.",
        )
        code_executor_agent = CodeExecutorAgent("code_executor", code_executor=code_executor)
        termination = TextMentionTermination("TERMINATE")

        # Create inner team (assistant + code executor)
        inner_team = RoundRobinGroupChat(
            participants=[assistant, code_executor_agent],
            termination_condition=termination,
            runtime=runtime,
            name="InnerTeam",
            description="Team that writes and executes code",
        )

        # Create reviewer agent
        reviewer = AssistantAgent(
            "agent3",
            model_client=model_client,
            description="A reviewer agent that reviews code.",
        )

        # Create outer team with nested inner team
        outer_team = SelectorGroupChat(
            participants=[inner_team, reviewer],
            model_client=model_client,
            termination_condition=termination,
            runtime=runtime,
        )

        messages: list[BaseAgentEvent | BaseChatMessage] = []
        result = None
        async for message in outer_team.run_stream(task="Write a program that prints 'Hello, world!'"):
            if isinstance(message, TaskResult):
                result = message
            else:
                messages.append(message)

        assert result is not None
        assert len(result.messages) >= 4
        assert isinstance(result.messages[0], TextMessage)
        assert result.messages[0].content == "Write a program that prints 'Hello, world!'"
        assert result.stop_reason is not None and "TERMINATE" in result.stop_reason