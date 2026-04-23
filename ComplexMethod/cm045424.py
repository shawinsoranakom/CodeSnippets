async def test_swarm_with_parallel_tool_calls(runtime: AgentRuntime | None) -> None:
    model_client = ReplayChatCompletionClient(
        [
            CreateResult(
                finish_reason="function_calls",
                content=[
                    FunctionCall(id="1", name="tool1", arguments="{}"),
                    FunctionCall(id="2", name="tool2", arguments="{}"),
                    FunctionCall(id="3", name="handoff_to_agent2", arguments=json.dumps({})),
                ],
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False,
            ),
            "Hello",
            "TERMINATE",
        ],
        model_info={
            "family": "gpt-4.1-nano",
            "function_calling": True,
            "json_output": True,
            "vision": True,
            "structured_output": True,
        },
    )

    expected_handoff_context: List[LLMMessage] = [
        AssistantMessage(
            source="agent1",
            content=[
                FunctionCall(id="1", name="tool1", arguments="{}"),
                FunctionCall(id="2", name="tool2", arguments="{}"),
            ],
        ),
        FunctionExecutionResultMessage(
            content=[
                FunctionExecutionResult(content="tool1", call_id="1", is_error=False, name="tool1"),
                FunctionExecutionResult(content="tool2", call_id="2", is_error=False, name="tool2"),
            ]
        ),
    ]

    def tool1() -> str:
        return "tool1"

    def tool2() -> str:
        return "tool2"

    agent1 = AssistantAgent(
        "agent1",
        model_client=model_client,
        handoffs=[Handoff(target="agent2", name="handoff_to_agent2", message="handoff to agent2")],
        tools=[tool1, tool2],
    )
    agent2 = AssistantAgent(
        "agent2",
        model_client=model_client,
    )
    termination = TextMentionTermination("TERMINATE")
    team = Swarm([agent1, agent2], termination_condition=termination, runtime=runtime)
    result = await team.run(task="task")
    assert len(result.messages) == 6
    assert compare_messages(result.messages[0], TextMessage(content="task", source="user"))
    assert isinstance(result.messages[1], ToolCallRequestEvent)
    assert isinstance(result.messages[2], ToolCallExecutionEvent)
    assert compare_messages(
        result.messages[3],
        HandoffMessage(
            content="handoff to agent2",
            target="agent2",
            source="agent1",
            context=expected_handoff_context,
        ),
    )
    assert isinstance(result.messages[4], TextMessage)
    assert result.messages[4].content == "Hello"
    assert result.messages[4].source == "agent2"
    assert isinstance(result.messages[5], TextMessage)
    assert result.messages[5].content == "TERMINATE"
    assert result.messages[5].source == "agent2"

    # Verify the tool calls are in agent2's context.
    agent2_model_ctx_messages = await agent2._model_context.get_messages()  # pyright: ignore
    assert agent2_model_ctx_messages[0] == UserMessage(content="task", source="user")
    assert agent2_model_ctx_messages[1] == expected_handoff_context[0]
    assert agent2_model_ctx_messages[2] == expected_handoff_context[1]