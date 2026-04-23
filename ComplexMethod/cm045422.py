async def test_swarm_handoff_using_tool_calls(runtime: AgentRuntime | None) -> None:
    model_client = ReplayChatCompletionClient(
        chat_completions=[
            CreateResult(
                finish_reason="function_calls",
                content=[FunctionCall(id="1", name="handoff_to_agent2", arguments=json.dumps({}))],
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
    agent1 = AssistantAgent(
        "agent1",
        model_client=model_client,
        handoffs=[Handoff(target="agent2", name="handoff_to_agent2", message="handoff to agent2")],
    )
    agent2 = _HandOffAgent("agent2", description="agent 2", next_agent="agent1")
    termination = TextMentionTermination("TERMINATE")
    team = Swarm([agent1, agent2], termination_condition=termination, runtime=runtime)
    result = await team.run(task="task")
    assert len(result.messages) == 7
    assert isinstance(result.messages[0], TextMessage)
    assert result.messages[0].content == "task"
    assert isinstance(result.messages[1], ToolCallRequestEvent)
    assert isinstance(result.messages[2], ToolCallExecutionEvent)
    assert isinstance(result.messages[3], HandoffMessage)
    assert isinstance(result.messages[4], HandoffMessage)
    assert isinstance(result.messages[5], TextMessage)
    assert isinstance(result.messages[6], TextMessage)
    assert result.messages[3].content == "handoff to agent2"
    assert result.messages[4].content == "Transferred to agent1."
    assert result.messages[5].content == "Hello"
    assert result.messages[6].content == "TERMINATE"
    assert result.stop_reason is not None and result.stop_reason == "Text 'TERMINATE' mentioned"

    # Test streaming.
    await agent1._model_context.clear()  # pyright: ignore
    model_client.reset()
    result_index = 0  # Include task message in result since output_task_messages=True by default
    await team.reset()
    stream = team.run_stream(task="task")
    async for message in stream:
        if isinstance(message, TaskResult):
            assert compare_task_results(message, result)
        else:
            assert compare_messages(message, result.messages[result_index])
            result_index += 1

    # Test Console
    await agent1._model_context.clear()  # pyright: ignore
    model_client.reset()
    await team.reset()
    result2 = await Console(team.run_stream(task="task"))
    assert compare_task_results(result2, result)