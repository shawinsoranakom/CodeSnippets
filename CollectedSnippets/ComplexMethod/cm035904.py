async def test_no_repo_mentioned_shows_button_and_dropdown(
        self,
        mock_send_message,
        mock_sio,
        slack_manager,
        slack_new_conversation_view,
    ):
        """Test that when no repo is mentioned, a button and dropdown are shown.

        The form shows:
        1. A "No Repository" button - immediately clickable without loading
        2. An external_select dropdown - for searching repositories dynamically
        """
        # Setup Redis mock
        mock_redis = AsyncMock()
        mock_sio.manager.redis = mock_redis

        # Setup: user message without any repo mention
        slack_new_conversation_view.user_msg = 'Hello, can you help me?'

        # Execute
        result = await slack_manager.is_job_requested(
            MagicMock(), slack_new_conversation_view
        )

        # Verify: should return False (no repo selected yet)
        assert result is False

        # Verify: send_message was called (for repo selector)
        mock_send_message.assert_called_once()
        call_args = mock_send_message.call_args

        # Should be the repo selection form with button + external_select
        message = call_args[0][0]
        assert isinstance(message, dict)
        assert message.get('text') == 'Choose a Repository:'

        blocks = message.get('blocks', [])
        actions_block = next((b for b in blocks if b.get('type') == 'actions'), None)
        assert actions_block is not None
        elements = actions_block.get('elements', [])

        # Should have 2 elements: button and external_select
        assert len(elements) == 2

        # First element: "No Repository" button (immediately available)
        assert elements[0].get('type') == 'button'
        assert elements[0].get('action_id').startswith('no_repository:')
        assert elements[0].get('value') == '-'

        # Second element: external_select for searching repos
        assert elements[1].get('type') == 'external_select'
        assert elements[1].get('action_id').startswith('repository_select:')