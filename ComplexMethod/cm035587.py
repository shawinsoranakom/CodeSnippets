async def test_add_message_creates_message_with_correct_data(
        self,
        service: SQLPendingMessageService,
        sample_content: list[TextContent],
    ):
        """Test that add_message creates a message with the expected fields."""
        # Arrange
        conversation_id = f'task-{uuid4().hex}'

        # Act
        response = await service.add_message(
            conversation_id=conversation_id,
            content=sample_content,
            role='user',
        )

        # Assert
        assert isinstance(response, PendingMessageResponse)
        assert response.queued is True
        assert response.id is not None

        # Verify the message was stored correctly
        messages = await service.get_pending_messages(conversation_id)
        assert len(messages) == 1
        assert messages[0].conversation_id == conversation_id
        assert len(messages[0].content) == 1
        assert isinstance(messages[0].content[0], TextContent)
        assert messages[0].content[0].text == sample_content[0].text
        assert messages[0].role == 'user'
        assert messages[0].created_at is not None