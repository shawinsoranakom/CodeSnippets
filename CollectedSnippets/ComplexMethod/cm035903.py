async def test_submit_feedback():
    """Test submitting feedback for a conversation."""
    # Create a mock database session
    mock_session = MagicMock()
    mock_session.commit = AsyncMock()

    # Test data
    feedback_data = FeedbackRequest(
        conversation_id='test-conversation-123',
        event_id=42,
        rating=5,
        reason='The agent was very helpful',
        metadata={'browser': 'Chrome', 'os': 'Windows'},
    )

    # Create async context manager for a_session_maker
    @asynccontextmanager
    async def mock_a_session_maker():
        yield mock_session

    # Mock a_session_maker
    with patch('server.routes.feedback.a_session_maker', mock_a_session_maker):
        # Call the function
        result = await submit_conversation_feedback(feedback_data)

        # Check response
        assert result == {
            'status': 'success',
            'message': 'Feedback submitted successfully',
        }

        # Verify the database operations were called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        # Verify the correct data was passed to add
        added_feedback = mock_session.add.call_args[0][0]
        assert isinstance(added_feedback, ConversationFeedback)
        assert added_feedback.conversation_id == 'test-conversation-123'
        assert added_feedback.event_id == 42
        assert added_feedback.rating == 5
        assert added_feedback.reason == 'The agent was very helpful'
        assert added_feedback.metadata == {'browser': 'Chrome', 'os': 'Windows'}