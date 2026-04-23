async def test_code_generation_and_execution_with_model_client() -> None:
    """
    Tests the code generation, execution and reflection pipeline using a model client.
    """

    language = "python"
    code = 'import math\n\nnumber = 42\nsquare_root = math.sqrt(number)\nprint("%0.3f" % (square_root,))'

    model_client = ReplayChatCompletionClient(
        [f"Here is the code to calculate the square root of 42:\n```{language}\n{code}```".strip(), "TERMINATE"]
    )

    agent = CodeExecutorAgent(
        name="code_executor_agent", code_executor=LocalCommandLineCodeExecutor(), model_client=model_client
    )

    messages = [
        TextMessage(
            content="Generate python code to calculate the square root of 42",
            source="assistant",
        )
    ]

    code_generation_event: CodeGenerationEvent | None = None
    code_execution_event: CodeExecutionEvent | None = None
    response: Response | None = None

    async for message in agent.on_messages_stream(messages, CancellationToken()):
        if isinstance(message, CodeGenerationEvent):
            code_block = message.code_blocks[0]
            assert code_block.code == code, "Code block does not match"
            assert code_block.language == language, "Language does not match"
            code_generation_event = message
        elif isinstance(message, CodeExecutionEvent):
            assert message.to_text().strip() == "6.481", f"Expected '6.481', got: {message.to_text().strip()}"
            code_execution_event = message
        elif isinstance(message, Response):
            assert isinstance(
                message.chat_message, TextMessage
            ), f"Expected TextMessage, got: {type(message.chat_message)}"
            assert (
                message.chat_message.source == "code_executor_agent"
            ), f"Expected source 'code_executor_agent', got: {message.chat_message.source}"
            response = message
        else:
            raise AssertionError(f"Unexpected message type: {type(message)}")

    assert code_generation_event is not None, "Code generation event was not received"
    assert code_execution_event is not None, "Code execution event was not received"
    assert response is not None, "Response was not received"