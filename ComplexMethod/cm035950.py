async def test_double_callback_processing(
        self,
        mock_request_summary,
        mock_web_client,
        mock_slack_team_store,
        slack_callback_processor,
        finish_event,
        event_callback,
    ):
        """Test that processor handles double callback correctly and processes both times."""
        conversation_id = uuid4()

        # Mock SlackTeamStore (async method)
        mock_store = MagicMock()
        mock_store.get_team_bot_token = AsyncMock(return_value='xoxb-test-token')
        mock_slack_team_store.return_value = mock_store

        # Mock successful summary generation
        mock_request_summary.return_value = 'Test summary from agent'

        # Mock Slack WebClient
        mock_slack_client = MagicMock()
        mock_slack_client.chat_postMessage.return_value = {'ok': True}
        mock_web_client.return_value = mock_slack_client

        # First callback
        result1 = await slack_callback_processor(
            conversation_id, event_callback, finish_event
        )

        # Second callback (should not exit, should process again)
        result2 = await slack_callback_processor(
            conversation_id, event_callback, finish_event
        )

        # Verify both callbacks succeeded
        assert result1 is not None
        assert result1.status == EventCallbackResultStatus.SUCCESS
        assert result1.detail == 'Test summary from agent'

        assert result2 is not None
        assert result2.status == EventCallbackResultStatus.SUCCESS
        assert result2.detail == 'Test summary from agent'

        # Verify both callbacks triggered summary requests and Slack posts
        assert mock_request_summary.call_count == 2
        assert mock_slack_client.chat_postMessage.call_count == 2