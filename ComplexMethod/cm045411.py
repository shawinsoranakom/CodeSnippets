async def test_round_robin_group_chat_with_tools(runtime: AgentRuntime | None) -> None:
    model_client = ReplayChatCompletionClient(
        chat_completions=[
            CreateResult(
                finish_reason="function_calls",
                content=[FunctionCall(id="1", name="pass", arguments=json.dumps({"input": "pass"}))],
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
    tool = FunctionTool(_pass_function, name="pass", description="pass function")
    tool_use_agent = AssistantAgent("tool_use_agent", model_client=model_client, tools=[tool])
    echo_agent = _EchoAgent("echo_agent", description="echo agent")
    termination = TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat(
        participants=[tool_use_agent, echo_agent], termination_condition=termination, runtime=runtime
    )
    result = await team.run(
        task="Write a program that prints 'Hello, world!'",
    )
    assert len(result.messages) == 8
    assert isinstance(result.messages[0], TextMessage)  # task
    assert isinstance(result.messages[1], ToolCallRequestEvent)  # tool call
    assert isinstance(result.messages[2], ToolCallExecutionEvent)  # tool call result
    assert isinstance(result.messages[3], ToolCallSummaryMessage)  # tool use agent response
    assert result.messages[3].content == "pass"  #  ensure the tool call was executed
    assert isinstance(result.messages[4], TextMessage)  # echo agent response
    assert isinstance(result.messages[5], TextMessage)  # tool use agent response
    assert isinstance(result.messages[6], TextMessage)  # echo agent response
    assert isinstance(result.messages[7], TextMessage)  # tool use agent response, that has TERMINATE
    assert result.messages[7].content == "TERMINATE"

    assert result.stop_reason is not None and result.stop_reason == "Text 'TERMINATE' mentioned"

    # Test streaming.
    await tool_use_agent._model_context.clear()  # pyright: ignore
    model_client.reset()
    result_index = 0  # Include task message in result since output_task_messages=True by default
    await team.reset()
    async for message in team.run_stream(
        task="Write a program that prints 'Hello, world!'",
    ):
        if isinstance(message, TaskResult):
            assert compare_task_results(message, result)
        else:
            assert compare_messages(message, result.messages[result_index])
            result_index += 1

    # Test Console.
    await tool_use_agent._model_context.clear()  # pyright: ignore
    model_client.reset()
    await team.reset()
    result2 = await Console(team.run_stream(task="Write a program that prints 'Hello, world!'"))
    assert compare_task_results(result2, result)