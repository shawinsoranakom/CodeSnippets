async def test_on_message_stream_mapping_url_citation(
    mock_project_client: MagicMock,
    fake_message: FakeMessageWithAnnotation | FakeMessageWithUrlCitationAnnotation,
    url: str,
    title: str,
) -> None:
    mock_project_client.agents.runs.create = AsyncMock(  # Corrected path and method name
        return_value=MagicMock(id="run-id", status=RunStatus.COMPLETED)
    )

    async def mock_messages_list_with_citation(
        **kwargs: Any,
    ) -> AsyncGenerator[FakeMessageWithAnnotation | FakeMessageWithUrlCitationAnnotation, None]:
        """Mock async generator for messages with citation"""
        yield fake_message

    mock_project_client.agents.messages.list = mock_messages_list_with_citation

    agent = create_agent(mock_project_client)

    messages = [TextMessage(content="Hello", source="user")]

    async for response in agent.on_messages_stream(messages):
        assert isinstance(response, Response)
        assert response.chat_message is not None
        assert response.chat_message.metadata is not None

        citations = json.loads(response.chat_message.metadata["citations"])
        assert citations is not None

        assert len(citations) == 1

        assert citations[0]["url"] == url
        assert citations[0]["title"] == title