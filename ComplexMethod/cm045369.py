async def test_agent_tool_stream() -> None:
    """Test running a task with AgentTool in streaming mode."""

    def _query_function() -> str:
        return "Test task"

    tool_agent_model_client = ReplayChatCompletionClient(
        [
            CreateResult(
                content=[FunctionCall(name="query_function", arguments="{}", id="1")],
                finish_reason="function_calls",
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False,
            ),
            "Summary from tool agent",
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
    tool_agent = AssistantAgent(
        name="tool_agent",
        model_client=tool_agent_model_client,
        tools=[_query_function],
        reflect_on_tool_use=True,
        description="An agent for testing",
    )
    tool = AgentTool(tool_agent)

    main_agent_model_client = ReplayChatCompletionClient(
        [
            CreateResult(
                content=[FunctionCall(id="1", name="tool_agent", arguments='{"task": "Input task from main agent"}')],
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
        model_client=main_agent_model_client,
        tools=[tool],
        reflect_on_tool_use=True,
        description="An agent for testing",
    )
    result = await main_agent.run(task="Input task from user", cancellation_token=CancellationToken())
    assert isinstance(result.messages[0], TextMessage)
    assert result.messages[0].content == "Input task from user"
    assert isinstance(result.messages[1], ToolCallRequestEvent)
    assert isinstance(result.messages[2], TextMessage)
    assert result.messages[2].content == "Input task from main agent"
    assert isinstance(result.messages[3], ToolCallRequestEvent)
    assert isinstance(result.messages[4], ToolCallExecutionEvent)
    assert isinstance(result.messages[5], TextMessage)
    assert result.messages[5].content == "Summary from tool agent"
    assert isinstance(result.messages[6], ToolCallExecutionEvent)
    assert result.messages[6].content[0].content == "tool_agent: Summary from tool agent"
    assert isinstance(result.messages[7], TextMessage)
    assert result.messages[7].content == "Summary from main agent"