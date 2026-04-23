async def test_budget_exceeded_error_logs_info_and_sends_friendly_message(
        self,
        mock_web_client_cls,
        mock_logger,
        mock_get_summary_instruction,
        mock_get_app_conversation_info_service,
        mock_get_sandbox_service,
        mock_get_httpx_client,
        mock_slack_team_store,
        slack_callback_processor,
        finish_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test that budget exceeded errors are logged at INFO level and user gets friendly message."""
        conversation_id = uuid4()

        # Mock SlackTeamStore
        mock_store = MagicMock()
        mock_store.get_team_bot_token = AsyncMock(return_value='xoxb-test-token')
        mock_slack_team_store.return_value = mock_store

        mock_get_summary_instruction.return_value = 'Please provide a summary'

        # Mock services
        mock_app_conversation_info_service = AsyncMock()
        mock_app_conversation_info_service.get_app_conversation_info.return_value = (
            mock_app_conversation_info
        )
        mock_get_app_conversation_info_service.return_value.__aenter__.return_value = (
            mock_app_conversation_info_service
        )

        mock_sandbox_service = AsyncMock()
        mock_sandbox_service.get_sandbox.return_value = mock_sandbox_info
        mock_get_sandbox_service.return_value.__aenter__.return_value = (
            mock_sandbox_service
        )

        # Simulate a budget exceeded error from the agent server
        budget_error_msg = (
            'HTTP 500 error: {"detail":"Internal Server Error",'
            '"exception":"litellm.BadRequestError: Litellm_proxyException - '
            'Budget has been exceeded! Current cost: 12.65, Max budget: 12.62"}'
        )
        mock_httpx_client = AsyncMock()
        mock_httpx_client.post.side_effect = Exception(budget_error_msg)
        mock_get_httpx_client.return_value.__aenter__.return_value = mock_httpx_client

        # Mock Slack WebClient
        mock_slack_client = MagicMock()
        mock_web_client_cls.return_value = mock_slack_client

        result = await slack_callback_processor(
            conversation_id, event_callback, finish_event
        )

        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR

        # Verify exception was NOT called (budget exceeded uses info instead)
        mock_logger.exception.assert_not_called()

        # Verify budget exceeded info log was called
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        budget_log_found = any('Budget exceeded' in call for call in info_calls)
        assert budget_log_found, f'Expected budget exceeded log, got: {info_calls}'

        # Verify user-friendly message was posted to Slack
        mock_slack_client.chat_postMessage.assert_called_once()
        call_kwargs = mock_slack_client.chat_postMessage.call_args[1]
        posted_message = call_kwargs.get('markdown_text', '')
        assert 'OpenHands encountered an error' in posted_message
        assert 'LLM budget has been exceeded' in posted_message
        assert 'please re-fill' in posted_message
        # Should NOT contain the raw error message
        assert 'litellm.BadRequestError' not in posted_message