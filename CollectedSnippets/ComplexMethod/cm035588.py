async def test_update_conversation_id_updates_all_matching_messages(
        self,
        service: SQLPendingMessageService,
        sample_content: list[TextContent],
    ):
        """Test that update_conversation_id updates all messages with the old ID."""
        # Arrange
        old_conversation_id = f'task-{uuid4().hex}'
        new_conversation_id = str(uuid4())
        unrelated_conversation_id = f'task-{uuid4().hex}'

        # Add messages to old conversation
        for _ in range(3):
            await service.add_message(old_conversation_id, sample_content)

        # Add message to unrelated conversation
        await service.add_message(unrelated_conversation_id, sample_content)

        # Act
        updated_count = await service.update_conversation_id(
            old_conversation_id, new_conversation_id
        )

        # Assert
        assert updated_count == 3

        # Verify old conversation has no messages
        assert await service.count_pending_messages(old_conversation_id) == 0

        # Verify new conversation has all messages
        messages = await service.get_pending_messages(new_conversation_id)
        assert len(messages) == 3
        for msg in messages:
            assert msg.conversation_id == new_conversation_id

        # Verify unrelated conversation is unchanged
        assert await service.count_pending_messages(unrelated_conversation_id) == 1