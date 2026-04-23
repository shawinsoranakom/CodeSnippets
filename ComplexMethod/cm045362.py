async def test_self_debugging_loop() -> None:
    """
    Tests self debugging loop when the model client responds with incorrect code.
    """
    language = "python"
    incorrect_code_block = """
numbers = [10, 20, 30, 40, 50]
mean = sum(numbers) / len(numbers
print("The mean is:", mean)
""".strip()
    incorrect_code_result = """
    mean = sum(numbers) / len(numbers
                             ^
SyntaxError: '(' was never closed
""".strip()
    correct_code_block = """
numbers = [10, 20, 30, 40, 50]
mean = sum(numbers) / len(numbers)
print("The mean is:", mean)
""".strip()
    correct_code_result = """
The mean is: 30.0
""".strip()

    model_client = ReplayChatCompletionClient(
        [
            f"""
Here is the code to calculate the mean of 10, 20, 30, 40, 50

```{language}
{incorrect_code_block}
```
""",
            """{"retry": "true", "reason": "Retry 1: It is a test environment"}""",
            f"""
Here is the updated code to calculate the mean of 10, 20, 30, 40, 50

```{language}
{correct_code_block}
```""",
            "Final Response",
            "TERMINATE",
        ],
        model_info=ModelInfo(
            vision=False,
            function_calling=False,
            json_output=True,
            family=ModelFamily.UNKNOWN,
            structured_output=True,
        ),
    )

    agent = CodeExecutorAgent(
        name="code_executor_agent",
        code_executor=LocalCommandLineCodeExecutor(),
        model_client=model_client,
        max_retries_on_error=1,
    )

    messages = [
        TextMessage(
            content="Calculate the mean of 10, 20, 30, 40, 50.",
            source="assistant",
        )
    ]

    incorrect_code_generation_event: CodeGenerationEvent | None = None
    correct_code_generation_event: CodeGenerationEvent | None = None
    retry_decision_event: CodeGenerationEvent | None = None
    incorrect_code_execution_event: CodeExecutionEvent | None = None
    correct_code_execution_event: CodeExecutionEvent | None = None
    response: Response | None = None

    message_id: int = 0
    async for message in agent.on_messages_stream(messages, CancellationToken()):
        if isinstance(message, CodeGenerationEvent) and message_id == 0:
            # Step 1: First code generation
            code_block = message.code_blocks[0]
            assert code_block.code.strip() == incorrect_code_block, "Incorrect code block does not match"
            assert code_block.language == language, "Language does not match"
            incorrect_code_generation_event = message

        elif isinstance(message, CodeExecutionEvent) and message_id == 1:
            # Step 2: First code execution
            assert (
                incorrect_code_result in message.to_text().strip()
            ), f"Expected {incorrect_code_result} in execution result, got: {message.to_text().strip()}"
            incorrect_code_execution_event = message

        elif isinstance(message, CodeGenerationEvent) and message_id == 2:
            # Step 3: Retry generation with proposed correction
            retry_response = "Attempt number: 1\nProposed correction: Retry 1: It is a test environment"
            assert (
                message.to_text().strip() == retry_response
            ), f"Expected {retry_response}, got: {message.to_text().strip()}"
            retry_decision_event = message

        elif isinstance(message, CodeGenerationEvent) and message_id == 3:
            # Step 4: Second retry code generation
            code_block = message.code_blocks[0]
            assert code_block.code.strip() == correct_code_block, "Correct code block does not match"
            assert code_block.language == language, "Language does not match"
            correct_code_generation_event = message

        elif isinstance(message, CodeExecutionEvent) and message_id == 4:
            # Step 5: Second retry code execution
            assert (
                message.to_text().strip() == correct_code_result
            ), f"Expected {correct_code_result} in execution result, got: {message.to_text().strip()}"
            correct_code_execution_event = message

        elif isinstance(message, Response) and message_id == 5:
            # Step 6: Final response
            assert isinstance(
                message.chat_message, TextMessage
            ), f"Expected TextMessage, got: {type(message.chat_message)}"
            assert (
                message.chat_message.source == "code_executor_agent"
            ), f"Expected source 'code_executor_agent', got: {message.chat_message.source}"
            response = message

        else:
            raise AssertionError(f"Unexpected message type: {type(message)}")

        message_id += 1

    assert incorrect_code_generation_event is not None, "Incorrect code generation event was not received"
    assert incorrect_code_execution_event is not None, "Incorrect code execution event was not received"
    assert retry_decision_event is not None, "Retry decision event was not received"
    assert correct_code_generation_event is not None, "Correct code generation event was not received"
    assert correct_code_execution_event is not None, "Correct code execution event was not received"
    assert response is not None, "Response was not received"