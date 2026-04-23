async def test_budget_exceeded_error_logs_info_and_sends_friendly_message(
        self,
        mock_logger,
        mock_saas_gitlab_service_cls,
        mock_get_summary_instruction,
        mock_get_httpx_client,
        mock_get_sandbox_service,
        mock_get_app_conversation_info_service,
        gitlab_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        """Test that budget exceeded errors are logged at INFO level and user gets friendly message."""
        conversation_id = uuid4()

        mock_httpx_client = await _setup_happy_path_services(
            mock_get_app_conversation_info_service,
            mock_get_sandbox_service,
            mock_get_httpx_client,
            mock_app_conversation_info,
            mock_sandbox_info,
        )
        # Simulate a budget exceeded error from the agent server
        budget_error_msg = (
            'HTTP 500 error: {"detail":"Internal Server Error",'
            '"exception":"litellm.BadRequestError: Litellm_proxyException - '
            'Budget has been exceeded! Current cost: 12.65, Max budget: 12.62"}'
        )
        mock_httpx_client.post.side_effect = Exception(budget_error_msg)
        mock_get_summary_instruction.return_value = 'Please provide a summary'

        mock_gitlab_service = AsyncMock()
        mock_saas_gitlab_service_cls.return_value = mock_gitlab_service

        result = await gitlab_callback_processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=conversation_state_update_event,
        )

        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR

        # Verify exception was NOT called (budget exceeded uses info instead)
        mock_logger.exception.assert_not_called()

        # Verify budget exceeded info log was called
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        budget_log_found = any('Budget exceeded' in call for call in info_calls)
        assert budget_log_found, f'Expected budget exceeded log, got: {info_calls}'

        # Verify user-friendly message was posted to GitLab
        mock_gitlab_service.reply_to_issue.assert_called_once()
        call_args = mock_gitlab_service.reply_to_issue.call_args
        posted_comment = call_args[0][3]  # 4th positional arg is the body
        assert 'OpenHands encountered an error' in posted_comment
        assert 'LLM budget has been exceeded' in posted_comment
        assert 'please re-fill' in posted_comment
        # Should NOT contain the raw error message
        assert 'litellm.BadRequestError' not in posted_comment