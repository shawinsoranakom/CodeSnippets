async def test_on_message_stream_mapping_file_citation(mock_project_client: MagicMock) -> None:
    mock_project_client.agents.create_run = AsyncMock(return_value=MagicMock(id="run-id", status=RunStatus.COMPLETED))

    expected_file_id = "file_id_1"
    expected_quote = "this part of a file"

    fake_message = FakeMessageWithFileCitationAnnotation(
        "msg-mock-1",
        "response-1",
        [FakeTextFileCitationAnnotation(FakeTextFileCitationDetails(expected_file_id, expected_quote))],
    )

    async def mock_messages_list_with_file_citation(
        **kwargs: Any,
    ) -> AsyncGenerator[FakeMessageWithFileCitationAnnotation, None]:
        """Mock async generator for messages with file citation"""
        yield fake_message

    mock_project_client.agents.messages.list = mock_messages_list_with_file_citation

    agent = create_agent(mock_project_client)

    messages = [TextMessage(content="Hello", source="user")]

    async for response in agent.on_messages_stream(messages):
        assert isinstance(response, Response)
        assert response.chat_message is not None
        assert response.chat_message.metadata is not None

        citations = json.loads(response.chat_message.metadata["citations"])
        assert citations is not None

        assert len(citations) == 1

        assert citations[0]["file_id"] == expected_file_id
        assert citations[0]["text"] == expected_quote