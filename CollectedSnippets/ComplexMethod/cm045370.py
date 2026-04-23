async def test_team_tool_stream() -> None:
    """Test running a task with TeamTool in streaming mode."""
    agent1 = _EchoAgent("Agent1", "An agent for testing")
    agent2 = _EchoAgent("Agent2", "Another agent for testing")
    termination = MaxMessageTermination(max_messages=3)
    team = RoundRobinGroupChat(
        [agent1, agent2],
        termination_condition=termination,
    )
    tool = TeamTool(
        team=team, name="team_tool", description="A team tool for testing", return_value_as_last_message=True
    )

    model_client = ReplayChatCompletionClient(
        [
            CreateResult(
                content=[FunctionCall(name="team_tool", arguments='{"task": "test task from main agent"}', id="1")],
                finish_reason="function_calls",
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False,
            ),
            "Summary from main agent",
        ],
        model_info={
            "family": "gpt-41",
            "function_calling": True,
            "json_output": True,
            "multiple_system_messages": True,
            "structured_output": True,
            "vision": True,
        },
    )
    main_agent = AssistantAgent(
        name="main_agent",
        model_client=model_client,
        tools=[tool],
        reflect_on_tool_use=True,
        description="An agent for testing",
    )
    result = await main_agent.run(task="test task from user", cancellation_token=CancellationToken())
    assert isinstance(result.messages[0], TextMessage)
    assert result.messages[0].content == "test task from user"
    assert isinstance(result.messages[1], ToolCallRequestEvent)
    assert isinstance(result.messages[2], TextMessage)
    assert result.messages[2].content == "test task from main agent"
    assert isinstance(result.messages[3], TextMessage)
    assert result.messages[3].content == "test task from main agent"
    assert result.messages[3].source == "Agent1"
    assert isinstance(result.messages[4], TextMessage)
    assert result.messages[4].content == "test task from main agent"
    assert result.messages[4].source == "Agent2"
    assert isinstance(result.messages[5], ToolCallExecutionEvent)
    assert result.messages[5].content[0].content == "test task from main agent"
    assert isinstance(result.messages[6], TextMessage)
    assert result.messages[6].content == "Summary from main agent"