async def test_model_client_with_function_calling(model: str, openai_client: OpenAIChatCompletionClient) -> None:
    # Test tool calling
    pass_tool = FunctionTool(_pass_function, name="pass_tool", description="pass session.")
    fail_tool = FunctionTool(_fail_function, name="fail_tool", description="fail session.")
    messages: List[LLMMessage] = [
        UserMessage(content="Call the pass tool with input 'task' summarize the result.", source="user")
    ]
    create_result = await openai_client.create(messages=messages, tools=[pass_tool, fail_tool])
    assert isinstance(create_result.content, list)
    assert len(create_result.content) == 1
    assert isinstance(create_result.content[0], FunctionCall)
    assert create_result.content[0].name == "pass_tool"
    assert json.loads(create_result.content[0].arguments) == {"input": "task"}
    assert create_result.finish_reason == "function_calls"
    assert create_result.usage is not None

    # Test reflection on tool call response.
    messages.append(AssistantMessage(content=create_result.content, source="assistant"))
    messages.append(
        FunctionExecutionResultMessage(
            content=[
                FunctionExecutionResult(
                    content="passed",
                    call_id=create_result.content[0].id,
                    is_error=False,
                    name=create_result.content[0].name,
                )
            ]
        )
    )
    create_result = await openai_client.create(messages=messages)
    assert isinstance(create_result.content, str)
    assert len(create_result.content) > 0

    # Test parallel tool calling
    messages = [
        UserMessage(
            content="Call both the pass tool with input 'task' and the fail tool also with input 'task' and summarize the result",
            source="user",
        )
    ]
    create_result = await openai_client.create(messages=messages, tools=[pass_tool, fail_tool])
    assert isinstance(create_result.content, list)
    assert len(create_result.content) == 2
    assert isinstance(create_result.content[0], FunctionCall)
    assert create_result.content[0].name == "pass_tool"
    assert json.loads(create_result.content[0].arguments) == {"input": "task"}
    assert isinstance(create_result.content[1], FunctionCall)
    assert create_result.content[1].name == "fail_tool"
    assert json.loads(create_result.content[1].arguments) == {"input": "task"}
    assert create_result.finish_reason == "function_calls"
    assert create_result.usage is not None

    # Test reflection on parallel tool call response.
    messages.append(AssistantMessage(content=create_result.content, source="assistant"))
    messages.append(
        FunctionExecutionResultMessage(
            content=[
                FunctionExecutionResult(
                    content="passed", call_id=create_result.content[0].id, is_error=False, name="pass_tool"
                ),
                FunctionExecutionResult(
                    content="failed", call_id=create_result.content[1].id, is_error=True, name="fail_tool"
                ),
            ]
        )
    )
    create_result = await openai_client.create(messages=messages)
    assert isinstance(create_result.content, str)
    assert len(create_result.content) > 0