async def test_azure_ai_chat_completion_client_create_stream(
    azure_client: AzureAIChatCompletionClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO):
        chunks: List[str | CreateResult] = []
        async for chunk in azure_client.create_stream(messages=[UserMessage(content="Hello", source="user")]):
            chunks.append(chunk)

        assert "LLMStreamStart" in caplog.text
        assert "LLMStreamEnd" in caplog.text

        final_result: str | CreateResult = chunks[-1]
        assert isinstance(final_result, CreateResult)
        assert isinstance(final_result.content, str)
        assert final_result.content in caplog.text

    assert chunks[0] == "Hello"
    assert chunks[1] == " Another Hello"
    assert chunks[2] == " Yet Another Hello"