async def test_sk_chat_completion_r1_content() -> None:
    async def mock_get_chat_message_contents(
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
        **kwargs: Any,
    ) -> list[ChatMessageContent]:
        return [
            ChatMessageContent(
                ai_model_id="r1",
                role=AuthorRole.ASSISTANT,
                metadata={"usage": {"prompt_tokens": 20, "completion_tokens": 9}},
                items=[TextContent(text="<think>Reasoning...</think> Hello!")],
                finish_reason=FinishReason.STOP,
            )
        ]

    async def mock_get_streaming_chat_message_contents(
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        chunks = ["<think>Reasoning...</think>", " Hello!"]
        for i, chunk in enumerate(chunks):
            yield [
                StreamingChatMessageContent(
                    choice_index=0,
                    inner_content=ChatCompletionChunk(
                        id=f"chatcmpl-{i}",
                        choices=[Choice(delta=ChoiceDelta(content=chunk), finish_reason=None, index=0)],
                        created=1736674044,
                        model="r1",
                        object="chat.completion.chunk",
                        service_tier="scale",
                        system_fingerprint="fingerprint",
                        usage=CompletionUsage(prompt_tokens=20, completion_tokens=9, total_tokens=29),
                    ),
                    ai_model_id="gpt-4o-mini",
                    metadata={"id": f"chatcmpl-{i}", "created": 1736674044},
                    role=AuthorRole.ASSISTANT,
                    items=[StreamingTextContent(choice_index=0, text=chunk)],
                    finish_reason=FinishReason.STOP if i == len(chunks) - 1 else None,
                )
            ]

    mock_client = AsyncMock(spec=AzureChatCompletion)
    mock_client.get_chat_message_contents = mock_get_chat_message_contents
    mock_client.get_streaming_chat_message_contents = mock_get_streaming_chat_message_contents

    kernel = Kernel(memory=NullMemory())

    adapter = SKChatCompletionAdapter(
        mock_client,
        kernel=kernel,
        model_info=ModelInfo(
            vision=False, function_calling=False, json_output=False, family=ModelFamily.R1, structured_output=False
        ),
    )

    result = await adapter.create(messages=[UserMessage(content="Say hello!", source="user")])
    assert result.finish_reason == "stop"
    assert result.content == "Hello!"
    assert result.thought == "Reasoning..."

    response_chunks: list[CreateResult | str] = []
    async for chunk in adapter.create_stream(messages=[UserMessage(content="Say hello!", source="user")]):
        response_chunks.append(chunk)
    assert len(response_chunks) > 0
    assert isinstance(response_chunks[-1], CreateResult)
    assert response_chunks[-1].finish_reason == "stop"
    assert response_chunks[-1].content == "Hello!"
    assert response_chunks[-1].thought == "Reasoning..."